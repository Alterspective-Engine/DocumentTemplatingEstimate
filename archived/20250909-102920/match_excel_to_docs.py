#!/usr/bin/env python3
"""
Match Excel template requirements to document complexity metrics
"""

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

def extract_excel_data(excel_path):
    """Extract data from Excel file without pandas"""
    z = zipfile.ZipFile(excel_path)
    
    # Get shared strings
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.parse(z.open('xl/sharedStrings.xml'))
        for si in tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            t = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
            shared_strings.append(t.text if t is not None and t.text else '')
    
    # Read first sheet
    sheet_data = []
    tree = ET.parse(z.open('xl/worksheets/sheet1.xml'))
    for row in tree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
        row_data = []
        for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
            v = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
            if v is not None:
                cell_type = cell.get('t', 'n')
                if cell_type == 's':  # shared string
                    idx = int(v.text)
                    row_data.append(shared_strings[idx] if idx < len(shared_strings) else '')
                else:
                    row_data.append(v.text)
            else:
                row_data.append('')
        if row_data and any(row_data):  # Skip empty rows
            sheet_data.append(row_data)
    
    return sheet_data

def load_complexity_data(base_path):
    """Load the complexity analysis we already generated"""
    complexity_file = base_path / 'document_complexity_analysis.json'
    if complexity_file.exists():
        with open(complexity_file, 'r') as f:
            return json.load(f)
    return None

def match_excel_to_document(excel_row, documents_data):
    """Match an Excel row to document complexity data"""
    if len(excel_row) < 3:
        return None
    
    template_code = excel_row[0].lower().strip()
    description = excel_row[1] if len(excel_row) > 1 else ''
    stated_complexity = excel_row[2] if len(excel_row) > 2 else ''
    
    # Try to find matching document
    for doc in documents_data:
        doc_name = doc['document_name'].lower()
        # Check if template code matches document name
        if template_code in doc_name or doc_name.startswith(template_code):
            return {
                'excel_template': template_code,
                'excel_description': description,
                'excel_complexity': stated_complexity,
                'matched_document': doc['document_name'],
                'document_id': doc['document_id'],
                'metrics': doc
            }
    
    return None

def analyze_complexity_accuracy(matches):
    """Compare Excel stated complexity vs calculated complexity"""
    accuracy_analysis = {
        'total_matches': len(matches),
        'complexity_comparison': [],
        'accuracy_rate': 0
    }
    
    complexity_mapping = {
        'Simple': ['Simple', 'Low'],
        'Medium': ['Medium'],
        'Complex': ['High', 'Very High']
    }
    
    correct_matches = 0
    
    for match in matches:
        excel_complexity = match['excel_complexity']
        calculated_complexity = match['metrics']['complexity_rating']
        
        # Check if complexities align
        is_match = False
        for excel_level, calc_levels in complexity_mapping.items():
            if excel_complexity == excel_level and calculated_complexity in calc_levels:
                is_match = True
                correct_matches += 1
                break
        
        accuracy_analysis['complexity_comparison'].append({
            'template': match['excel_template'],
            'excel_stated': excel_complexity,
            'calculated': calculated_complexity,
            'match': is_match,
            'total_fields': match['metrics']['total_fields'],
            'complexity_score': match['metrics']['total_complexity_score']
        })
    
    if accuracy_analysis['total_matches'] > 0:
        accuracy_analysis['accuracy_rate'] = (correct_matches / accuracy_analysis['total_matches']) * 100
    
    return accuracy_analysis

def main():
    base_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData')
    excel_file = base_path / 'Super Template Requirements_received 23072025.xlsx'
    
    print("=== Excel to Document Complexity Matching ===\n")
    
    # Extract Excel data
    print("Extracting Excel data...")
    excel_data = extract_excel_data(excel_file)
    print(f"Found {len(excel_data)} rows in Excel")
    
    # Load complexity data
    print("Loading complexity analysis...")
    complexity_data = load_complexity_data(base_path)
    if not complexity_data:
        print("Error: Complexity analysis not found. Run analyze_complexity.py first.")
        return
    
    documents = complexity_data['documents']
    print(f"Loaded {len(documents)} document complexity profiles")
    
    # Match Excel rows to documents
    print("\nMatching Excel templates to documents...")
    matches = []
    unmatched = []
    
    # Skip header row
    for i, row in enumerate(excel_data[1:], 1):
        if len(row) >= 3 and row[0]:  # Has template code
            match = match_excel_to_document(row, documents)
            if match:
                matches.append(match)
                print(f"  ✓ Matched: {row[0]} → {match['matched_document']}")
            else:
                unmatched.append({
                    'row': i,
                    'template': row[0],
                    'description': row[1] if len(row) > 1 else '',
                    'complexity': row[2] if len(row) > 2 else ''
                })
    
    print(f"\nMatching Results:")
    print(f"  Matched: {len(matches)}/{len(excel_data)-1} templates")
    print(f"  Unmatched: {len(unmatched)} templates")
    
    # Analyze complexity accuracy
    print("\n=== Complexity Analysis Comparison ===")
    accuracy = analyze_complexity_accuracy(matches)
    
    print(f"Overall Accuracy: {accuracy['accuracy_rate']:.1f}%")
    print("\nComplexity Comparison (First 20 matches):")
    print("-" * 100)
    print(f"{'Template':<15} {'Excel Stated':<15} {'Calculated':<15} {'Match':<10} {'Fields':<10} {'Score':<10}")
    print("-" * 100)
    
    for comp in accuracy['complexity_comparison'][:20]:
        match_str = "✓" if comp['match'] else "✗"
        print(f"{comp['template']:<15} {comp['excel_stated']:<15} {comp['calculated']:<15} "
              f"{match_str:<10} {comp['total_fields']:<10} {comp['complexity_score']:<10}")
    
    # Generate detailed complexity report for matched templates
    print("\n=== Detailed Complexity Metrics for Matched Templates ===")
    print("-" * 120)
    print(f"{'Template':<10} {'Description':<40} {'Fields':<8} {'Unique':<8} {'Reuse':<8} "
          f"{'IFs':<6} {'Unbound':<8} {'Score':<8}")
    print("-" * 120)
    
    for match in matches[:30]:  # Show first 30
        m = match['metrics']
        desc = match['excel_description'][:39] if match['excel_description'] else ''
        print(f"{match['excel_template']:<10} {desc:<40} {m['total_fields']:<8} "
              f"{m['unique_fields']:<8} {m['reusable_fields']:<8} "
              f"{m['if_statements']:<6} {m['unbound_fields']:<8} "
              f"{m['total_complexity_score']:<8}")
    
    # Save comprehensive matching report
    output = {
        'summary': {
            'total_excel_templates': len(excel_data) - 1,
            'matched_templates': len(matches),
            'unmatched_templates': len(unmatched),
            'match_rate': (len(matches) / (len(excel_data) - 1)) * 100 if len(excel_data) > 1 else 0,
            'complexity_accuracy': accuracy['accuracy_rate']
        },
        'matched_templates': []
    }
    
    for match in matches:
        output['matched_templates'].append({
            'excel_template': match['excel_template'],
            'excel_description': match['excel_description'],
            'excel_complexity': match['excel_complexity'],
            'matched_document': match['matched_document'],
            'complexity_metrics': {
                'total_fields': match['metrics']['total_fields'],
                'unique_fields': match['metrics']['unique_fields'],
                'reusable_fields': match['metrics']['reusable_fields'],
                'docvariable_fields': match['metrics']['docvariable_fields'],
                'mergefield_fields': match['metrics']['mergefield_fields'],
                'if_statements': match['metrics']['if_statements'],
                'unbound_fields': match['metrics']['unbound_fields'],
                'user_input_fields': match['metrics']['user_input_fields'],
                'calculated_fields': match['metrics']['calculated_fields'],
                'complex_fields': match['metrics']['complex_fields'],
                'total_complexity_score': match['metrics']['total_complexity_score'],
                'calculated_complexity': match['metrics']['complexity_rating']
            }
        })
    
    output['unmatched_templates'] = unmatched
    
    # Save report
    report_file = base_path / 'excel_document_matching_report.json'
    with open(report_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Create CSV for easy Excel viewing
    csv_file = base_path / 'excel_complexity_comparison.csv'
    with open(csv_file, 'w') as f:
        # Header
        f.write('Excel_Template,Excel_Description,Excel_Complexity,Matched_Document,'
                'Total_Fields,Unique_Fields,Reusable_Fields,IF_Statements,Unbound_Fields,'
                'User_Input_Fields,Calculated_Fields,Complexity_Score,Calculated_Complexity\n')
        
        # Data rows
        for match in matches:
            m = match['metrics']
            row = [
                match['excel_template'],
                match['excel_description'].replace(',', ';'),
                match['excel_complexity'],
                match['matched_document'],
                str(m['total_fields']),
                str(m['unique_fields']),
                str(m['reusable_fields']),
                str(m['if_statements']),
                str(m['unbound_fields']),
                str(m['user_input_fields']),
                str(m['calculated_fields']),
                str(m['total_complexity_score']),
                m['complexity_rating']
            ]
            f.write(','.join(row) + '\n')
    
    print(f"CSV comparison saved to: {csv_file}")
    
    # Print summary statistics
    print("\n=== Summary Statistics for Matched Templates ===")
    if matches:
        total_fields = sum(m['metrics']['total_fields'] for m in matches)
        total_unique = sum(m['metrics']['unique_fields'] for m in matches)
        total_reusable = sum(m['metrics']['reusable_fields'] for m in matches)
        total_unbound = sum(m['metrics']['unbound_fields'] for m in matches)
        
        print(f"Total Fields Across Matched Templates: {total_fields}")
        print(f"Total Unique Fields: {total_unique}")
        print(f"Total Reusable Fields: {total_reusable}")
        print(f"Total Unbound Fields: {total_unbound}")
        print(f"Average Fields per Template: {total_fields/len(matches):.1f}")
        print(f"Field Reusability Rate: {(total_reusable/total_unique*100) if total_unique > 0 else 0:.1f}%")
        print(f"Unbound Field Rate: {(total_unbound/total_fields*100) if total_fields > 0 else 0:.1f}%")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Document Complexity Analysis without external dependencies
Analyzes document fields and calculates complexity metrics
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def load_json_data(base_path):
    """Load JSON data from SQLExport"""
    data = {}
    json_files = {
        'documents': 'SQLExport/dbo_Documents.json',
        'fields': 'SQLExport/dbo_Fields.json',
        'doc_fields': 'SQLExport/dbo_DocumentFields.json',
        'combined': 'SQLExport/combined_analysis.json'
    }
    
    for key, file_path in json_files.items():
        full_path = Path(base_path) / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                data[key] = json.load(f)
    
    return data

def analyze_field_complexity(field_code):
    """Analyze complexity of a field code"""
    if not field_code:
        return {}
    
    field_code_upper = field_code.upper()
    
    metrics = {
        'is_docvariable': 'DOCVARIABLE' in field_code_upper,
        'is_mergefield': 'MERGEFIELD' in field_code_upper,
        'has_if_statement': field_code.strip().upper().startswith('IF') or ' IF ' in field_code_upper,
        'has_formatting': '\\*' in field_code,
        'has_user_input': '!' in field_code or 'SELECT' in field_code_upper,
        'has_calculation': any(op in field_code for op in ['+', '-', '*', '/', '=', '>', '<']),
        'has_nested_logic': field_code.count('IF') > 1,
        'field_length': len(field_code),
        'is_complex': False
    }
    
    # Determine complexity score
    complexity_score = sum([
        metrics['has_if_statement'] * 3,
        metrics['has_nested_logic'] * 2,
        metrics['has_user_input'] * 2,
        metrics['has_calculation'] * 2,
        metrics['is_docvariable'],
        metrics['is_mergefield'],
        metrics['has_formatting']
    ])
    
    metrics['is_complex'] = complexity_score >= 3
    metrics['complexity_score'] = complexity_score
    
    return metrics

def calculate_document_metrics(doc_id, doc_name, json_data):
    """Calculate comprehensive complexity metrics for a document"""
    metrics = {
        'document_id': doc_id,
        'document_name': doc_name,
        'total_fields': 0,
        'unique_fields': 0,
        'reusable_fields': 0,
        'docvariable_fields': 0,
        'mergefield_fields': 0,
        'if_statements': 0,
        'nested_if_statements': 0,
        'unbound_fields': 0,
        'user_input_fields': 0,
        'calculated_fields': 0,
        'complex_fields': 0,
        'avg_field_length': 0,
        'max_field_length': 0,
        'total_complexity_score': 0,
        'avg_complexity_score': 0
    }
    
    # Get all fields for this document
    doc_field_ids = []
    field_counts = {}
    
    for rel in json_data.get('doc_fields', {}).get('data', []):
        if rel['DocumentID'] == doc_id:
            field_id = rel['FieldID']
            doc_field_ids.append(field_id)
            field_counts[field_id] = rel.get('Count', 1)
    
    # Analyze each field
    field_codes_seen = defaultdict(int)
    total_length = 0
    max_length = 0
    
    for field_id in doc_field_ids:
        # Find the field details
        field_data = None
        for field in json_data.get('fields', {}).get('data', []):
            if field['FieldID'] == field_id:
                field_data = field
                break
        
        if not field_data:
            continue
            
        field_code = field_data.get('FieldCode', '')
        field_result = field_data.get('FieldResult')
        
        # Track unique vs reusable
        field_codes_seen[field_code] += field_counts.get(field_id, 1)
        
        # Analyze field complexity
        complexity = analyze_field_complexity(field_code)
        
        # Update metrics
        metrics['total_fields'] += field_counts.get(field_id, 1)
        
        if complexity.get('is_docvariable'):
            metrics['docvariable_fields'] += 1
        if complexity.get('is_mergefield'):
            metrics['mergefield_fields'] += 1
        if complexity.get('has_if_statement'):
            metrics['if_statements'] += 1
        if complexity.get('has_nested_logic'):
            metrics['nested_if_statements'] += 1
        if field_result is None or field_result == '' or field_result == ' ':
            metrics['unbound_fields'] += 1
        if complexity.get('has_user_input'):
            metrics['user_input_fields'] += 1
        if complexity.get('has_calculation'):
            metrics['calculated_fields'] += 1
        if complexity.get('is_complex'):
            metrics['complex_fields'] += 1
        
        field_length = complexity.get('field_length', 0)
        total_length += field_length
        max_length = max(max_length, field_length)
        metrics['total_complexity_score'] += complexity.get('complexity_score', 0)
    
    # Calculate unique vs reusable
    metrics['unique_fields'] = len(field_codes_seen)
    metrics['reusable_fields'] = sum(1 for code, count in field_codes_seen.items() if count > 1)
    
    # Calculate averages
    if metrics['total_fields'] > 0:
        metrics['avg_field_length'] = round(total_length / metrics['total_fields'], 2)
        metrics['avg_complexity_score'] = round(metrics['total_complexity_score'] / metrics['total_fields'], 2)
    
    metrics['max_field_length'] = max_length
    
    # Calculate overall complexity rating
    if metrics['total_complexity_score'] == 0:
        metrics['complexity_rating'] = 'Simple'
    elif metrics['total_complexity_score'] < 10:
        metrics['complexity_rating'] = 'Low'
    elif metrics['total_complexity_score'] < 30:
        metrics['complexity_rating'] = 'Medium'
    elif metrics['total_complexity_score'] < 50:
        metrics['complexity_rating'] = 'High'
    else:
        metrics['complexity_rating'] = 'Very High'
    
    return metrics

def analyze_precedent_complexity(manifest_path):
    """Analyze complexity of a precedent from its manifest"""
    try:
        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        metrics = {
            'has_script': '_' in str(manifest_path),
            'has_multi_prec': 'PrecMultiPrec' in content and '>true<' in content,
            'has_reminder': 'PrecReminder' in content and '>true<' in content,
            'has_time_recording': 'PrecTimeRec' in content,
            'has_sql_update': 'PrecUpdateSQL' in content and content.count('PrecUpdateSQL') > 1,
            'precedent_type': '',
            'category': ''
        }
        
        # Extract precedent type
        type_match = re.search(r'<PrecType>([^<]+)</PrecType>', content)
        if type_match:
            metrics['precedent_type'] = type_match.group(1)
            
        # Extract category
        cat_match = re.search(r'<PrecCategory>([^<]+)</PrecCategory>', content)
        if cat_match:
            metrics['category'] = cat_match.group(1)
            
        return metrics
    except:
        return {}

def main():
    base_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData')
    
    print("=== Document Complexity Analysis ===\n")
    
    # Load JSON data
    print("Loading JSON data...")
    json_data = load_json_data(base_path)
    
    # Get all documents
    all_docs = json_data.get('documents', {}).get('data', [])
    print(f"Total documents found: {len(all_docs)}")
    
    # Calculate metrics for all documents
    print("\nAnalyzing document complexity...")
    all_metrics = []
    
    for doc in all_docs:
        metrics = calculate_document_metrics(
            doc['DocumentID'], 
            doc['Filename'],
            json_data
        )
        all_metrics.append(metrics)
    
    # Sort by complexity score
    all_metrics.sort(key=lambda x: x['total_complexity_score'], reverse=True)
    
    # Print top 10 most complex documents
    print("\n=== Top 10 Most Complex Documents ===")
    print("-" * 100)
    print(f"{'Rank':<5} {'Document Name':<30} {'Total Fields':<12} {'Complexity':<12} {'Rating':<10}")
    print("-" * 100)
    
    for i, metrics in enumerate(all_metrics[:10], 1):
        print(f"{i:<5} {metrics['document_name'][:29]:<30} {metrics['total_fields']:<12} "
              f"{metrics['total_complexity_score']:<12} {metrics['complexity_rating']:<10}")
    
    # Calculate summary statistics
    print("\n=== Summary Statistics ===")
    print("-" * 50)
    
    total_docs = len(all_metrics)
    total_fields = sum(m['total_fields'] for m in all_metrics)
    avg_fields = total_fields / total_docs if total_docs > 0 else 0
    
    complexity_distribution = defaultdict(int)
    for m in all_metrics:
        complexity_distribution[m['complexity_rating']] += 1
    
    print(f"Total Documents: {total_docs}")
    print(f"Total Fields: {total_fields}")
    print(f"Average Fields per Document: {avg_fields:.2f}")
    print(f"\nComplexity Distribution:")
    for rating in ['Simple', 'Low', 'Medium', 'High', 'Very High']:
        count = complexity_distribution[rating]
        percentage = (count / total_docs * 100) if total_docs > 0 else 0
        print(f"  {rating:<10}: {count:>4} ({percentage:>5.1f}%)")
    
    # Field type analysis
    print("\n=== Field Type Analysis ===")
    print("-" * 50)
    
    total_docvar = sum(m['docvariable_fields'] for m in all_metrics)
    total_merge = sum(m['mergefield_fields'] for m in all_metrics)
    total_if = sum(m['if_statements'] for m in all_metrics)
    total_unbound = sum(m['unbound_fields'] for m in all_metrics)
    total_user_input = sum(m['user_input_fields'] for m in all_metrics)
    total_calculated = sum(m['calculated_fields'] for m in all_metrics)
    
    print(f"DOCVARIABLE Fields: {total_docvar}")
    print(f"MERGEFIELD Fields: {total_merge}")
    print(f"IF Statements: {total_if}")
    print(f"Unbound Fields: {total_unbound}")
    print(f"User Input Fields: {total_user_input}")
    print(f"Calculated Fields: {total_calculated}")
    
    # Reusability analysis
    print("\n=== Field Reusability Analysis ===")
    print("-" * 50)
    
    total_unique = sum(m['unique_fields'] for m in all_metrics)
    total_reusable = sum(m['reusable_fields'] for m in all_metrics)
    
    print(f"Total Unique Field Codes: {total_unique}")
    print(f"Total Reusable Fields: {total_reusable}")
    print(f"Reusability Rate: {(total_reusable/total_unique*100) if total_unique > 0 else 0:.1f}%")
    
    # Save detailed results
    output_file = base_path / 'document_complexity_analysis.json'
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_documents': total_docs,
                'total_fields': total_fields,
                'avg_fields_per_document': avg_fields,
                'complexity_distribution': dict(complexity_distribution),
                'field_types': {
                    'docvariable': total_docvar,
                    'mergefield': total_merge,
                    'if_statements': total_if,
                    'unbound': total_unbound,
                    'user_input': total_user_input,
                    'calculated': total_calculated
                },
                'reusability': {
                    'unique_fields': total_unique,
                    'reusable_fields': total_reusable,
                    'reusability_rate': (total_reusable/total_unique*100) if total_unique > 0 else 0
                }
            },
            'documents': all_metrics
        }, f, indent=2)
    
    print(f"\nDetailed analysis saved to: {output_file}")
    
    # Create CSV output for Excel viewing
    csv_output = base_path / 'document_complexity_metrics.csv'
    with open(csv_output, 'w') as f:
        # Write header
        headers = ['document_id', 'document_name', 'total_fields', 'unique_fields', 'reusable_fields',
                   'docvariable_fields', 'mergefield_fields', 'if_statements', 'unbound_fields',
                   'user_input_fields', 'calculated_fields', 'complex_fields', 'total_complexity_score',
                   'complexity_rating']
        f.write(','.join(headers) + '\n')
        
        # Write data
        for m in all_metrics:
            row = [str(m.get(h, '')) for h in headers]
            f.write(','.join(row) + '\n')
    
    print(f"CSV metrics saved to: {csv_output}")
    
    return all_metrics

if __name__ == "__main__":
    metrics = main()
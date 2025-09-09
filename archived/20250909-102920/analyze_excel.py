#!/usr/bin/env python3
"""
Excel to Document Mapping and Complexity Analysis
Analyzes Excel template requirements and matches them to document data
"""

import json
import pandas as pd
import re
from pathlib import Path

def load_excel_data(excel_path):
    """Load and analyze the Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"Excel loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"Error loading Excel: {e}")
        return None

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
                print(f"Loaded {key}: {full_path}")
    
    return data

def analyze_field_complexity(field_code):
    """Analyze complexity of a field code"""
    metrics = {
        'is_docvariable': 'DOCVARIABLE' in field_code,
        'is_mergefield': 'MERGEFIELD' in field_code,
        'has_if_statement': field_code.strip().startswith('IF') or ' IF ' in field_code,
        'has_formatting': '\\*' in field_code,
        'has_user_input': '!' in field_code or 'select' in field_code.lower(),
        'has_calculation': any(op in field_code for op in ['+', '-', '*', '/', '=', '>', '<']),
        'field_length': len(field_code),
        'is_complex': False
    }
    
    # Determine if complex
    complexity_score = sum([
        metrics['has_if_statement'] * 3,
        metrics['has_user_input'] * 2,
        metrics['has_calculation'] * 2,
        metrics['is_docvariable'],
        metrics['is_mergefield'],
        metrics['has_formatting']
    ])
    
    metrics['is_complex'] = complexity_score >= 3
    metrics['complexity_score'] = complexity_score
    
    return metrics

def match_document_to_excel(excel_row, documents_data):
    """Try to match an Excel row to a document"""
    # Extract potential document identifiers from Excel row
    row_dict = excel_row.to_dict()
    
    # Look for document name patterns in various columns
    matches = []
    for col, value in row_dict.items():
        if pd.notna(value) and isinstance(value, str):
            # Check if value matches document naming patterns
            if re.match(r'sup\d+[a-z]?', str(value).lower()):
                # Search for matching document
                for doc in documents_data.get('data', []):
                    if str(value).lower() in doc['Filename'].lower():
                        matches.append(doc)
    
    return matches

def calculate_document_metrics(doc_id, json_data):
    """Calculate complexity metrics for a document"""
    metrics = {
        'document_id': doc_id,
        'total_fields': 0,
        'unique_fields': 0,
        'reusable_fields': 0,
        'docvariable_fields': 0,
        'mergefield_fields': 0,
        'if_statements': 0,
        'unbound_fields': 0,
        'user_input_fields': 0,
        'calculated_fields': 0,
        'complex_fields': 0,
        'avg_field_length': 0,
        'total_complexity_score': 0
    }
    
    # Get all fields for this document
    doc_fields = []
    for rel in json_data.get('doc_fields', {}).get('data', []):
        if rel['DocumentID'] == doc_id:
            field_id = rel['FieldID']
            # Find the field details
            for field in json_data.get('fields', {}).get('data', []):
                if field['FieldID'] == field_id:
                    field['Count'] = rel['Count']
                    doc_fields.append(field)
                    break
    
    metrics['total_fields'] = len(doc_fields)
    
    # Analyze each field
    field_codes_seen = {}
    total_length = 0
    
    for field in doc_fields:
        field_code = field.get('FieldCode', '')
        field_result = field.get('FieldResult')
        
        # Track unique vs reusable
        if field_code in field_codes_seen:
            field_codes_seen[field_code] += 1
        else:
            field_codes_seen[field_code] = 1
        
        # Analyze field complexity
        complexity = analyze_field_complexity(field_code)
        
        # Update metrics
        if complexity['is_docvariable']:
            metrics['docvariable_fields'] += 1
        if complexity['is_mergefield']:
            metrics['mergefield_fields'] += 1
        if complexity['has_if_statement']:
            metrics['if_statements'] += 1
        if field_result is None or field_result == '':
            metrics['unbound_fields'] += 1
        if complexity['has_user_input']:
            metrics['user_input_fields'] += 1
        if complexity['has_calculation']:
            metrics['calculated_fields'] += 1
        if complexity['is_complex']:
            metrics['complex_fields'] += 1
        
        total_length += complexity['field_length']
        metrics['total_complexity_score'] += complexity['complexity_score']
    
    # Calculate unique vs reusable
    metrics['unique_fields'] = len(field_codes_seen)
    metrics['reusable_fields'] = sum(1 for count in field_codes_seen.values() if count > 1)
    
    # Calculate average field length
    if metrics['total_fields'] > 0:
        metrics['avg_field_length'] = total_length / metrics['total_fields']
    
    return metrics

def main():
    base_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData')
    excel_file = base_path / 'Super Template Requirements_received 23072025.xlsx'
    
    print("=== Excel and Document Complexity Analysis ===\n")
    
    # Load Excel data
    excel_df = load_excel_data(excel_file)
    if excel_df is None:
        return
    
    # Display first few rows to understand structure
    print("\n=== Excel Data Preview ===")
    print(excel_df.head())
    print(f"\nData types:")
    print(excel_df.dtypes)
    
    # Save Excel as CSV for easier viewing
    csv_path = base_path / 'excel_data.csv'
    excel_df.to_csv(csv_path, index=False)
    print(f"\nExcel data saved to: {csv_path}")
    
    # Load JSON data
    print("\n=== Loading JSON Data ===")
    json_data = load_json_data(base_path)
    
    # Analyze document complexity
    print("\n=== Analyzing Document Complexity ===")
    
    # Get all documents
    all_docs = json_data.get('documents', {}).get('data', [])
    print(f"Total documents: {len(all_docs)}")
    
    # Calculate metrics for sample documents
    sample_metrics = []
    for doc in all_docs[:10]:  # Analyze first 10 documents as sample
        metrics = calculate_document_metrics(doc['DocumentID'], json_data)
        metrics['filename'] = doc['Filename']
        sample_metrics.append(metrics)
    
    # Create metrics DataFrame
    metrics_df = pd.DataFrame(sample_metrics)
    print("\n=== Sample Document Complexity Metrics ===")
    print(metrics_df.to_string())
    
    # Save full analysis
    all_metrics = []
    for doc in all_docs:
        metrics = calculate_document_metrics(doc['DocumentID'], json_data)
        metrics['filename'] = doc['Filename']
        all_metrics.append(metrics)
    
    full_metrics_df = pd.DataFrame(all_metrics)
    metrics_csv_path = base_path / 'document_complexity_metrics.csv'
    full_metrics_df.to_csv(metrics_csv_path, index=False)
    print(f"\nFull metrics saved to: {metrics_csv_path}")
    
    # Summary statistics
    print("\n=== Complexity Summary Statistics ===")
    print(full_metrics_df.describe())
    
    # Try to match Excel rows to documents
    print("\n=== Attempting Excel to Document Matching ===")
    matches_found = 0
    for idx, row in excel_df.iterrows():
        matches = match_document_to_excel(row, json_data.get('documents', {}))
        if matches:
            matches_found += 1
            print(f"Row {idx}: Found {len(matches)} document matches")
    
    print(f"\nTotal Excel rows with document matches: {matches_found}/{len(excel_df)}")
    
    return excel_df, full_metrics_df

if __name__ == "__main__":
    excel_df, metrics_df = main()
#!/usr/bin/env python3
"""
Verify that all columns from SQL tables have been imported into JSON files
"""

import json
import os
from collections import defaultdict

def check_column_completeness():
    """Compare columns in JSON data with table schemas"""
    
    # Load table schemas (what columns exist in SQL)
    with open('newSQL/table_schemas.json', 'r', encoding='utf-8') as f:
        schemas = json.load(f)
    
    # Load actual data files
    with open('newSQL/documents.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    with open('newSQL/fields.json', 'r', encoding='utf-8') as f:
        fields = json.load(f)
    
    with open('newSQL/documentfields.json', 'r', encoding='utf-8') as f:
        doc_fields = json.load(f)
    
    # Organize schema by table
    schema_by_table = defaultdict(list)
    for col in schemas:
        table = col['TABLE_NAME']
        schema_by_table[table].append({
            'column': col['COLUMN_NAME'],
            'type': col['DATA_TYPE'],
            'nullable': col['IS_NULLABLE'],
            'max_length': col['CHARACTER_MAXIMUM_LENGTH']
        })
    
    # Get actual columns from JSON data
    actual_columns = {
        'Documents': set(),
        'Fields': set(),
        'DocumentFields': set()
    }
    
    # Get all unique keys from documents
    for doc in documents:
        actual_columns['Documents'].update(doc.keys())
    
    # Get all unique keys from fields
    for field in fields:
        actual_columns['Fields'].update(field.keys())
    
    # Get all unique keys from documentfields
    for df in doc_fields:
        actual_columns['DocumentFields'].update(df.keys())
    
    print("=" * 80)
    print("COLUMN COMPLETENESS VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # Compare for each table
    tables_to_check = ['Documents', 'Fields', 'DocumentFields']
    
    all_columns_present = True
    detailed_report = []
    
    for table in tables_to_check:
        print(f"\n📊 TABLE: {table}")
        print("-" * 60)
        
        # Get schema columns
        schema_cols = set(col['column'] for col in schema_by_table[table])
        actual_cols = actual_columns[table]
        
        # Find differences
        missing_in_json = schema_cols - actual_cols
        extra_in_json = actual_cols - schema_cols
        present_in_both = schema_cols & actual_cols
        
        print(f"  Schema columns: {len(schema_cols)}")
        print(f"  JSON columns: {len(actual_cols)}")
        print(f"  Matched columns: {len(present_in_both)}")
        
        if missing_in_json:
            all_columns_present = False
            print(f"\n  ❌ MISSING COLUMNS (in SQL but not in JSON):")
            for col in sorted(missing_in_json):
                # Find column details
                col_info = next((c for c in schema_by_table[table] if c['column'] == col), None)
                if col_info:
                    nullable = "NULL" if col_info['nullable'] == 'YES' else "NOT NULL"
                    print(f"     - {col} ({col_info['type']}, {nullable})")
                else:
                    print(f"     - {col}")
        else:
            print(f"\n  ✅ All SQL columns are present in JSON")
        
        if extra_in_json:
            print(f"\n  ℹ️  EXTRA COLUMNS (in JSON but not in schema):")
            for col in sorted(extra_in_json):
                print(f"     - {col}")
        
        # Show column listing
        print(f"\n  📋 COLUMNS IN BOTH:")
        sorted_cols = sorted(present_in_both)
        for i in range(0, len(sorted_cols), 3):
            cols = sorted_cols[i:i+3]
            print(f"     {', '.join(cols)}")
        
        # Detailed schema info for this table
        detailed_report.append({
            'table': table,
            'schema_columns': sorted(schema_cols),
            'json_columns': sorted(actual_cols),
            'missing': sorted(missing_in_json),
            'extra': sorted(extra_in_json),
            'matched': sorted(present_in_both)
        })
    
    # Check data samples to verify actual data presence
    print("\n" + "=" * 80)
    print("DATA SAMPLE VERIFICATION")
    print("=" * 80)
    
    print("\n📝 Sample data from each table (first record):")
    
    if documents:
        print("\nDocuments table sample:")
        first_doc = documents[0]
        for key, value in list(first_doc.items())[:5]:
            val_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {key}: {val_str}")
        print(f"  ... and {len(first_doc) - 5} more columns")
    
    if fields:
        print("\nFields table sample:")
        first_field = fields[0]
        for key, value in list(first_field.items())[:5]:
            val_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {key}: {val_str}")
        print(f"  ... and {len(first_field) - 5} more columns")
    
    if doc_fields:
        print("\nDocumentFields table sample:")
        first_df = doc_fields[0]
        for key, value in list(first_df.items())[:5]:
            val_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            print(f"  {key}: {val_str}")
        if len(first_df) > 5:
            print(f"  ... and {len(first_df) - 5} more columns")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if all_columns_present:
        print("\n✅ SUCCESS: All columns from SQL tables are present in JSON files!")
    else:
        print("\n⚠️  WARNING: Some columns from SQL tables are missing in JSON files.")
        print("This might be intentional if certain columns were excluded from the export.")
    
    # Save detailed report
    report_file = 'newSQL/column_verification_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return summary statistics
    total_missing = sum(len(r['missing']) for r in detailed_report)
    total_extra = sum(len(r['extra']) for r in detailed_report)
    total_matched = sum(len(r['matched']) for r in detailed_report)
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total matched columns: {total_matched}")
    print(f"  Total missing columns: {total_missing}")
    print(f"  Total extra columns: {total_extra}")
    
    return detailed_report

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    os.chdir('..')  # Go back to project root
    check_column_completeness()
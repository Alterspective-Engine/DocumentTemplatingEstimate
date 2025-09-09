#!/usr/bin/env python3
"""
Validate JSON files and ensure data completeness
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime

def load_json_file(filename):
    """Load and validate a JSON file"""
    filepath = os.path.join('newSQL', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return True, data, None
    except FileNotFoundError:
        return False, None, f"File not found: {filepath}"
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON in {filename}: {str(e)}"
    except Exception as e:
        return False, None, f"Error reading {filename}: {str(e)}"

def validate_json_structure(data, filename):
    """Validate JSON structure and data types"""
    issues = []
    
    if not isinstance(data, (list, dict)):
        issues.append(f"{filename}: Expected list or dict, got {type(data).__name__}")
        return issues
    
    if isinstance(data, list):
        if len(data) == 0:
            issues.append(f"{filename}: Warning - empty list")
        else:
            # Check first item structure
            first_item = data[0]
            if not isinstance(first_item, dict):
                issues.append(f"{filename}: List items should be dictionaries")
            
            # Check for None values
            none_count = 0
            for i, item in enumerate(data):
                for key, value in item.items():
                    if value is None:
                        none_count += 1
            
            if none_count > 0:
                issues.append(f"{filename}: Found {none_count} NULL values (this is normal)")
    
    return issues

def check_data_relationships(documents, fields, doc_fields, field_analysis):
    """Cross-check relationships between tables"""
    issues = []
    stats = {}
    
    # Extract IDs
    doc_ids = set(doc['DocumentID'] for doc in documents)
    field_ids = set(field['FieldID'] for field in fields)
    
    # Check DocumentFields relationships
    orphan_doc_refs = []
    orphan_field_refs = []
    
    for df in doc_fields:
        if df['DocumentID'] not in doc_ids:
            orphan_doc_refs.append(df['DocumentID'])
        if df['FieldID'] not in field_ids:
            orphan_field_refs.append(df['FieldID'])
    
    if orphan_doc_refs:
        issues.append(f"DocumentFields has {len(set(orphan_doc_refs))} references to non-existent documents")
    if orphan_field_refs:
        issues.append(f"DocumentFields has {len(set(orphan_field_refs))} references to non-existent fields")
    
    # Statistics
    stats['total_documents'] = len(documents)
    stats['total_fields'] = len(fields)
    stats['total_relationships'] = len(doc_fields)
    stats['unique_documents_with_fields'] = len(set(df['DocumentID'] for df in doc_fields))
    stats['unique_fields_used'] = len(set(df['FieldID'] for df in doc_fields))
    stats['avg_fields_per_document'] = len(doc_fields) / len(documents) if documents else 0
    
    # Check field_analysis data
    if field_analysis:
        fa_doc_ids = set(fa['documentid'] for fa in field_analysis if fa['documentid'])
        unmatched_fa_docs = fa_doc_ids - doc_ids
        if unmatched_fa_docs:
            issues.append(f"Field analysis has {len(unmatched_fa_docs)} references to non-existent documents")
        
        # Count field categories
        category_counts = defaultdict(int)
        for fa in field_analysis:
            category_counts[fa.get('field_category', 'Unknown')] += 1
        stats['field_categories'] = dict(category_counts)
    
    return issues, stats

def check_data_completeness(documents, fields, doc_fields):
    """Check for data completeness and potential issues"""
    issues = []
    warnings = []
    
    # Check for required fields in documents
    doc_missing_fields = []
    for doc in documents:
        if not doc.get('DocumentID'):
            doc_missing_fields.append('DocumentID')
        if not doc.get('Filename'):  # Note: capital F, lowercase n
            doc_missing_fields.append('Filename')
    
    if doc_missing_fields:
        issues.append(f"Documents missing required fields: {set(doc_missing_fields)}")
    
    # Check for required fields in Fields table
    field_missing = []
    for field in fields:
        if not field.get('FieldID'):
            field_missing.append('FieldID')
        if not field.get('FieldCode'):
            field_missing.append('FieldCode')
    
    if field_missing:
        issues.append(f"Fields missing required data: {set(field_missing)}")
    
    # Check for documents without any fields
    docs_with_fields = set(df['DocumentID'] for df in doc_fields)
    docs_without_fields = set(doc['DocumentID'] for doc in documents) - docs_with_fields
    if docs_without_fields:
        warnings.append(f"{len(docs_without_fields)} documents have no associated fields")
    
    # Check for unused fields
    used_fields = set(df['FieldID'] for df in doc_fields)
    unused_fields = set(field['FieldID'] for field in fields) - used_fields
    if unused_fields:
        warnings.append(f"{len(unused_fields)} fields are not used in any document")
    
    return issues, warnings

def analyze_field_types(field_analysis):
    """Analyze field types and complexity"""
    analysis = {
        'total_entries': len(field_analysis),
        'by_category': defaultdict(int),
        'null_fieldcodes': 0,
        'null_results': 0,
        'unique_fieldcodes': set(),
        'documents_with_fields': set()
    }
    
    for fa in field_analysis:
        category = fa.get('field_category', 'Unknown')
        analysis['by_category'][category] += 1
        
        if fa.get('fieldcode') is None:
            analysis['null_fieldcodes'] += 1
        else:
            analysis['unique_fieldcodes'].add(fa['fieldcode'])
        
        if fa.get('fieldresult') is None:
            analysis['null_results'] += 1
        
        if fa.get('documentid'):
            analysis['documents_with_fields'].add(fa['documentid'])
    
    analysis['unique_fieldcodes'] = len(analysis['unique_fieldcodes'])
    analysis['documents_with_fields'] = len(analysis['documents_with_fields'])
    analysis['by_category'] = dict(analysis['by_category'])
    
    return analysis

def generate_report(all_issues, all_stats, field_type_analysis):
    """Generate validation report"""
    report = []
    report.append("=" * 60)
    report.append("JSON DATA VALIDATION REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # File validation status
    report.append("FILE VALIDATION STATUS:")
    report.append("-" * 40)
    for filename, status in all_issues['file_status'].items():
        icon = "✅" if status == "Valid" else "❌"
        report.append(f"{icon} {filename}: {status}")
    report.append("")
    
    # Data statistics
    report.append("DATA STATISTICS:")
    report.append("-" * 40)
    for key, value in all_stats.items():
        if key == 'field_categories':
            report.append(f"\nField Categories:")
            for cat, count in value.items():
                report.append(f"  - {cat}: {count:,}")
        elif key == 'avg_fields_per_document':
            report.append(f"{key}: {value:.2f}")
        else:
            report.append(f"{key}: {value:,}")
    report.append("")
    
    # Field type analysis
    report.append("FIELD TYPE ANALYSIS:")
    report.append("-" * 40)
    report.append(f"Total field entries: {field_type_analysis['total_entries']:,}")
    report.append(f"Unique field codes: {field_type_analysis['unique_fieldcodes']:,}")
    report.append(f"Documents with analyzed fields: {field_type_analysis['documents_with_fields']:,}")
    report.append(f"Null field codes: {field_type_analysis['null_fieldcodes']:,}")
    report.append(f"Null field results: {field_type_analysis['null_results']:,}")
    report.append("\nField Categories Breakdown:")
    for cat, count in sorted(field_type_analysis['by_category'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / field_type_analysis['total_entries']) * 100
        report.append(f"  - {cat}: {count:,} ({percentage:.1f}%)")
    report.append("")
    
    # Issues and warnings
    if all_issues['structure_issues']:
        report.append("STRUCTURE ISSUES:")
        report.append("-" * 40)
        for issue in all_issues['structure_issues']:
            report.append(f"⚠️  {issue}")
        report.append("")
    
    if all_issues['relationship_issues']:
        report.append("RELATIONSHIP ISSUES:")
        report.append("-" * 40)
        for issue in all_issues['relationship_issues']:
            report.append(f"⚠️  {issue}")
        report.append("")
    
    if all_issues['completeness_issues']:
        report.append("COMPLETENESS ISSUES:")
        report.append("-" * 40)
        for issue in all_issues['completeness_issues']:
            report.append(f"❌ {issue}")
        report.append("")
    
    if all_issues['warnings']:
        report.append("WARNINGS:")
        report.append("-" * 40)
        for warning in all_issues['warnings']:
            report.append(f"⚠️  {warning}")
        report.append("")
    
    # Summary
    report.append("VALIDATION SUMMARY:")
    report.append("-" * 40)
    
    critical_issues = len(all_issues['completeness_issues'])
    total_warnings = len(all_issues['warnings']) + len(all_issues['structure_issues']) + len(all_issues['relationship_issues'])
    
    if critical_issues == 0 and total_warnings == 0:
        report.append("✅ All data validated successfully!")
        report.append("✅ No issues found")
        report.append("✅ Data is complete and properly structured")
    elif critical_issues == 0:
        report.append("✅ Data is valid with minor warnings")
        report.append(f"⚠️  {total_warnings} warnings found (see above)")
    else:
        report.append("❌ Critical issues found")
        report.append(f"❌ {critical_issues} critical issues need attention")
        report.append(f"⚠️  {total_warnings} additional warnings")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)

def main():
    """Main validation function"""
    print("\nStarting JSON validation...\n")
    
    all_issues = {
        'file_status': {},
        'structure_issues': [],
        'relationship_issues': [],
        'completeness_issues': [],
        'warnings': []
    }
    all_stats = {}
    
    # Load all JSON files
    files_to_validate = [
        'documents.json',
        'fields.json',
        'documentfields.json',
        'field_analysis.json',
        'table_schemas.json',
        'row_counts.json'
    ]
    
    loaded_data = {}
    
    # Step 1: Load and validate JSON files
    print("Step 1: Loading and validating JSON files...")
    for filename in files_to_validate:
        success, data, error = load_json_file(filename)
        if success:
            loaded_data[filename] = data
            all_issues['file_status'][filename] = "Valid"
            print(f"  ✅ {filename} - Valid JSON")
            
            # Validate structure
            structure_issues = validate_json_structure(data, filename)
            all_issues['structure_issues'].extend(structure_issues)
        else:
            all_issues['file_status'][filename] = error
            print(f"  ❌ {filename} - {error}")
    
    # Step 2: Cross-check relationships if core files loaded
    if all(f in loaded_data for f in ['documents.json', 'fields.json', 'documentfields.json']):
        print("\nStep 2: Cross-checking data relationships...")
        
        documents = loaded_data['documents.json']
        fields = loaded_data['fields.json']
        doc_fields = loaded_data['documentfields.json']
        field_analysis = loaded_data.get('field_analysis.json', [])
        
        relationship_issues, stats = check_data_relationships(
            documents, fields, doc_fields, field_analysis
        )
        all_issues['relationship_issues'].extend(relationship_issues)
        all_stats.update(stats)
        
        # Step 3: Check data completeness
        print("\nStep 3: Checking data completeness...")
        completeness_issues, warnings = check_data_completeness(
            documents, fields, doc_fields
        )
        all_issues['completeness_issues'].extend(completeness_issues)
        all_issues['warnings'].extend(warnings)
        
        # Step 4: Analyze field types
        print("\nStep 4: Analyzing field types...")
        field_type_analysis = analyze_field_types(field_analysis)
    else:
        print("\n❌ Cannot perform relationship checks - missing core files")
        field_type_analysis = {'total_entries': 0, 'by_category': {}}
    
    # Verify row counts match
    if 'row_counts.json' in loaded_data:
        row_counts = loaded_data['row_counts.json']
        for table_name, expected_count in row_counts.items():
            json_file = f"{table_name.lower()}.json"
            if json_file in loaded_data:
                actual_count = len(loaded_data[json_file])
                if actual_count != expected_count:
                    all_issues['completeness_issues'].append(
                        f"Row count mismatch for {table_name}: expected {expected_count}, got {actual_count}"
                    )
    
    # Generate report
    print("\nGenerating validation report...")
    report = generate_report(all_issues, all_stats, field_type_analysis)
    
    # Save report
    report_file = 'newSQL/validation_report.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Display report
    print("\n" + report)
    print(f"\nReport saved to: {report_file}")
    
    # Return exit code
    if all_issues['completeness_issues']:
        return 1  # Critical issues
    elif all_issues['warnings'] or all_issues['structure_issues'] or all_issues['relationship_issues']:
        return 0  # Warnings only
    else:
        return 0  # All good

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    os.chdir('..')  # Go back to project root
    sys.exit(main())
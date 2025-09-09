#!/usr/bin/env python3
"""
Analyze Superannuation Insurance documents (files starting with 'Sup')
"""

import json
import os
from collections import defaultdict

def analyze_superannuation_docs():
    """Analyze documents related to Superannuation"""
    
    # Load documents
    with open('newSQL/documents.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    # Load field analysis for more details
    with open('newSQL/field_analysis.json', 'r', encoding='utf-8') as f:
        field_analysis = json.load(f)
    
    # Load document fields
    with open('newSQL/documentfields.json', 'r', encoding='utf-8') as f:
        doc_fields = json.load(f)
    
    # Categorize documents
    sup_docs = []
    other_docs = []
    
    for doc in documents:
        filename = doc.get('Filename', '').lower()
        if filename.startswith('sup'):
            sup_docs.append(doc)
        else:
            other_docs.append(doc)
    
    # Analyze sup documents in detail
    sup_patterns = defaultdict(int)
    sup_by_prefix = defaultdict(list)
    
    for doc in sup_docs:
        filename = doc.get('Filename', '')
        # Extract pattern (e.g., sup001, sup002a, etc.)
        if filename.lower().startswith('sup'):
            # Get the first part before any extension
            base_name = filename.split('.')[0]
            # Group by numeric prefix
            prefix = base_name[:6] if len(base_name) >= 6 else base_name
            sup_by_prefix[prefix].append(doc)
            
            # Count file extensions
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
                sup_patterns[ext] += 1
    
    # Count fields per sup document
    sup_doc_ids = set(doc['DocumentID'] for doc in sup_docs)
    sup_field_count = defaultdict(int)
    
    for df in doc_fields:
        if df['DocumentID'] in sup_doc_ids:
            sup_field_count[df['DocumentID']] += 1
    
    # Analyze field categories for sup documents
    sup_field_categories = defaultdict(int)
    total_sup_fields = 0
    
    for fa in field_analysis:
        if fa.get('documentid') in sup_doc_ids:
            category = fa.get('field_category', 'Unknown')
            sup_field_categories[category] += 1
            total_sup_fields += 1
    
    # Print comprehensive report
    print("=" * 70)
    print("SUPERANNUATION INSURANCE DOCUMENTS ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"  Total documents in database: {len(documents)}")
    print(f"  Superannuation documents (starting with 'Sup'): {len(sup_docs)}")
    print(f"  Other documents: {len(other_docs)}")
    print(f"  Percentage that are Superannuation: {(len(sup_docs)/len(documents)*100):.1f}%")
    print()
    
    print("📁 FILE TYPES:")
    for ext, count in sorted(sup_patterns.items(), key=lambda x: x[1], reverse=True):
        print(f"  .{ext}: {count} files")
    print()
    
    print("📝 SAMPLE SUPERANNUATION DOCUMENTS:")
    # Show first 10 and last 5 for pattern understanding
    sorted_sup = sorted(sup_docs, key=lambda x: x.get('Filename', ''))
    print("  First 10:")
    for i, doc in enumerate(sorted_sup[:10], 1):
        field_count = sup_field_count.get(doc['DocumentID'], 0)
        print(f"    {i}. {doc.get('Filename')} (ID: {doc['DocumentID']}, Fields: {field_count})")
    
    if len(sorted_sup) > 10:
        print("  ...")
        print("  Last 5:")
        for i, doc in enumerate(sorted_sup[-5:], len(sorted_sup)-4):
            field_count = sup_field_count.get(doc['DocumentID'], 0)
            print(f"    {i}. {doc.get('Filename')} (ID: {doc['DocumentID']}, Fields: {field_count})")
    print()
    
    print("📊 FIELD STATISTICS FOR SUPERANNUATION DOCUMENTS:")
    print(f"  Total fields in Sup documents: {total_sup_fields}")
    if sup_docs:
        print(f"  Average fields per Sup document: {total_sup_fields/len(sup_docs):.1f}")
    
    # Documents with most fields
    top_docs_by_fields = sorted(
        [(doc_id, count) for doc_id, count in sup_field_count.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    print(f"\n  Top 5 Sup documents by field count:")
    for doc_id, count in top_docs_by_fields:
        doc_name = next((d['Filename'] for d in sup_docs if d['DocumentID'] == doc_id), 'Unknown')
        print(f"    - {doc_name}: {count} fields")
    print()
    
    print("📈 FIELD CATEGORIES IN SUPERANNUATION DOCUMENTS:")
    for category, count in sorted(sup_field_categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_sup_fields * 100) if total_sup_fields > 0 else 0
        print(f"  {category}: {count} ({percentage:.1f}%)")
    print()
    
    # Identify document groups/series
    print("📂 DOCUMENT SERIES/GROUPS:")
    series = defaultdict(list)
    for doc in sup_docs:
        filename = doc.get('Filename', '')
        if filename.lower().startswith('sup'):
            # Extract numeric part
            import re
            match = re.match(r'sup(\d+)', filename.lower())
            if match:
                number = int(match.group(1))
                # Group by hundreds
                series_group = f"sup{(number // 100) * 100:03d}-sup{(number // 100) * 100 + 99:03d}"
                series[series_group].append(filename)
    
    for series_name, docs in sorted(series.items()):
        if docs:  # Only show non-empty series
            print(f"  {series_name}: {len(docs)} documents")
    print()
    
    # Check for specific patterns that might indicate document types
    print("🔍 DOCUMENT NAMING PATTERNS:")
    patterns = {
        'Letters (a,b,c suffix)': [],
        'Numeric only': [],
        'With underscores': [],
        'With spaces': [],
        'Other patterns': []
    }
    
    for doc in sup_docs:
        filename = doc.get('Filename', '')
        base = filename.split('.')[0].lower()
        
        if re.match(r'sup\d+[a-z]$', base):
            patterns['Letters (a,b,c suffix)'].append(filename)
        elif re.match(r'sup\d+$', base):
            patterns['Numeric only'].append(filename)
        elif '_' in base:
            patterns['With underscores'].append(filename)
        elif ' ' in filename:
            patterns['With spaces'].append(filename)
        else:
            patterns['Other patterns'].append(filename)
    
    for pattern_name, files in patterns.items():
        if files:
            print(f"  {pattern_name}: {len(files)} documents")
            if len(files) <= 3:
                for f in files[:3]:
                    print(f"    - {f}")
    
    print()
    print("=" * 70)
    
    # Save detailed list to file
    output_file = 'newSQL/superannuation_documents.json'
    sup_summary = {
        'total_documents': len(documents),
        'superannuation_documents': len(sup_docs),
        'percentage': round(len(sup_docs)/len(documents)*100, 2),
        'field_statistics': {
            'total_fields': total_sup_fields,
            'average_fields_per_doc': round(total_sup_fields/len(sup_docs), 1) if sup_docs else 0,
            'field_categories': dict(sup_field_categories)
        },
        'file_types': dict(sup_patterns),
        'document_list': [
            {
                'DocumentID': doc['DocumentID'],
                'Filename': doc.get('Filename'),
                'FileSize': doc.get('FileSize'),
                'FileCreateDate': doc.get('FileCreateDate'),
                'FileModifyDate': doc.get('FileModifyDate'),
                'FieldCount': sup_field_count.get(doc['DocumentID'], 0)
            }
            for doc in sorted(sup_docs, key=lambda x: x.get('Filename', ''))
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sup_summary, f, indent=2, default=str)
    
    print(f"✅ Detailed analysis saved to: {output_file}")
    
    return sup_summary

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    os.chdir('..')  # Go back to project root
    analyze_superannuation_docs()
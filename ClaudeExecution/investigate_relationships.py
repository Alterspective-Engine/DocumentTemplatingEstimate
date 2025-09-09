import json
import pandas as pd
from pathlib import Path
import re

print("=" * 80)
print("INVESTIGATING DATA RELATIONSHIPS")
print("=" * 80)

# Load all data sources
print("\n1. Loading all data sources...")

# Client Requirements
df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
print(f"\nClient Requirements: {len(df_client)} rows")
print(f"Columns: {df_client.columns.tolist()}")
print("\nSample Client Requirement titles:")
for title in df_client['Current Title'].head(10):
    print(f"  - {title}")

# SQL Documents
with open('../ImportantData/SQLExport/dbo_Documents.json', 'r') as f:
    docs_json = json.load(f)
    sql_docs = docs_json.get('data', [])

print(f"\nSQL Documents: {len(sql_docs)} documents")
print("Sample SQL document filenames:")
for doc in sql_docs[:10]:
    print(f"  - {doc['Filename']} (ID: {doc['DocumentID']})")

# SQL Fields
with open('../ImportantData/SQLExport/dbo_Fields.json', 'r') as f:
    fields_json = json.load(f)
    sql_fields = fields_json.get('data', [])

print(f"\nSQL Fields: {len(sql_fields)} fields")
if sql_fields:
    print(f"Field structure: {list(sql_fields[0].keys())}")

# SQL DocumentFields (the mapping)
with open('../ImportantData/SQLExport/dbo_DocumentFields.json', 'r') as f:
    doc_fields_json = json.load(f)
    sql_doc_fields = doc_fields_json.get('data', [])

print(f"\nSQL DocumentFields mappings: {len(sql_doc_fields)} mappings")
if sql_doc_fields:
    print(f"Mapping structure: {list(sql_doc_fields[0].keys())}")

print("\n" + "=" * 80)
print("2. ANALYZING RELATIONSHIPS")
print("=" * 80)

# Check how SQL document names relate to Client Requirements
print("\n2.1 Comparing naming patterns...")

# Extract base names from SQL documents
sql_doc_names = {}
for doc in sql_docs:
    filename = doc['Filename']
    # Remove extension
    base_name = filename.replace('.dot', '').replace('.docx', '')
    sql_doc_names[base_name.lower()] = doc

print(f"\nUnique SQL document base names: {len(sql_doc_names)}")

# Check matches with Client Requirements
matches = []
no_matches = []

for idx, row in df_client.iterrows():
    title = row['Current Title']
    title_lower = title.lower()
    
    if title_lower in sql_doc_names:
        matches.append({
            'ClientTitle': title,
            'SQLFilename': sql_doc_names[title_lower]['Filename'],
            'DocumentID': sql_doc_names[title_lower]['DocumentID']
        })
    else:
        no_matches.append(title)

print(f"\n2.2 MATCHING RESULTS:")
print(f"  Direct matches: {len(matches)} ({len(matches)/len(df_client)*100:.1f}%)")
print(f"  No matches: {len(no_matches)} ({len(no_matches)/len(df_client)*100:.1f}%)")

if matches:
    print("\nSample matches:")
    for match in matches[:5]:
        print(f"  {match['ClientTitle']} -> {match['SQLFilename']} (ID: {match['DocumentID']})")

if no_matches:
    print(f"\nSample non-matches:")
    for title in no_matches[:10]:
        print(f"  - {title}")

# Analyze DocumentFields to understand field distribution
print("\n" + "=" * 80)
print("3. ANALYZING FIELD DISTRIBUTION")
print("=" * 80)

# Count fields per document
doc_field_counts = {}
for mapping in sql_doc_fields:
    doc_id = mapping['DocumentID']
    if doc_id not in doc_field_counts:
        doc_field_counts[doc_id] = 0
    doc_field_counts[doc_id] += mapping.get('Count', 1)

print(f"\nDocuments with field mappings: {len(doc_field_counts)}")
if doc_field_counts:
    counts = list(doc_field_counts.values())
    print(f"Field count statistics:")
    print(f"  Min fields: {min(counts)}")
    print(f"  Max fields: {max(counts)}")
    print(f"  Avg fields: {sum(counts)/len(counts):.1f}")
    print(f"  Total field instances: {sum(counts)}")

# Check which SQL documents have field data
docs_with_fields = set(doc_field_counts.keys())
all_doc_ids = set(doc['DocumentID'] for doc in sql_docs)
docs_without_fields = all_doc_ids - docs_with_fields

print(f"\nSQL Documents WITH field data: {len(docs_with_fields)}")
print(f"SQL Documents WITHOUT field data: {len(docs_without_fields)}")

# Show some documents with field data
print("\nSample documents with field data:")
for doc_id in list(docs_with_fields)[:10]:
    doc_name = next((d['Filename'] for d in sql_docs if d['DocumentID'] == doc_id), 'Unknown')
    field_count = doc_field_counts.get(doc_id, 0)
    print(f"  ID {doc_id}: {doc_name} - {field_count} field instances")

# Analyze field categories by looking at field codes
print("\n" + "=" * 80)
print("4. ANALYZING FIELD CATEGORIES")
print("=" * 80)

field_categories = {
    'IF Statements': [],
    'Document Variables': [],
    'Merge Fields': [],
    'Include Text': [],
    'References': [],
    'Precedent Scripts': [],
    'Other': []
}

for field in sql_fields:
    field_id = field['FieldID']
    field_code = field.get('FieldCode', '')
    
    categorized = False
    
    # Check for IF statements (must check first as they often contain DOCVARIABLE)
    if re.search(r'\bIF\b', field_code, re.IGNORECASE):
        field_categories['IF Statements'].append(field_id)
        categorized = True
    # Document Variables (not inside IF)
    elif 'DOCVARIABLE' in field_code:
        field_categories['Document Variables'].append(field_id)
        categorized = True
    # Merge Fields
    elif 'MERGEFIELD' in field_code:
        field_categories['Merge Fields'].append(field_id)
        categorized = True
    # Include Text
    elif 'INCLUDETEXT' in field_code:
        field_categories['Include Text'].append(field_id)
        categorized = True
    # References
    elif 'REF' in field_code and 'MERGEFIELD' not in field_code:
        field_categories['References'].append(field_id)
        categorized = True
    # Check for scripts (often start with underscore or contain script patterns)
    elif field_code.strip().startswith('_') or 'Script' in field_code:
        field_categories['Precedent Scripts'].append(field_id)
        categorized = True
    
    if not categorized:
        field_categories['Other'].append(field_id)

print("Field category breakdown:")
for category, field_ids in field_categories.items():
    print(f"  {category}: {len(field_ids)} fields")

# Now link everything together properly
print("\n" + "=" * 80)
print("5. CREATING PROPER LINKAGE")
print("=" * 80)

# For each matched document, get its field breakdown
linked_data = []

for idx, row in df_client.iterrows():
    title = row['Current Title']
    title_lower = title.lower()
    
    result = {
        'ClientTitle': title,
        'Description': row['Description'],
        'OriginalComplexity': row['Complexity'],
        'SQLDocumentID': None,
        'SQLFilename': None,
        'TotalFieldInstances': 0,
        'UniqueFields': 0
    }
    
    # Initialize category counts
    for category in field_categories.keys():
        result[f'{category}_Count'] = 0
        result[f'{category}_Unique'] = 0
        result[f'{category}_Reused'] = 0
    
    # Check if we have SQL data for this document
    if title_lower in sql_doc_names:
        sql_doc = sql_doc_names[title_lower]
        doc_id = sql_doc['DocumentID']
        
        result['SQLDocumentID'] = doc_id
        result['SQLFilename'] = sql_doc['Filename']
        
        # Get all field mappings for this document
        doc_field_mappings = [m for m in sql_doc_fields if m['DocumentID'] == doc_id]
        
        # Track field usage across all documents for reuse analysis
        field_usage = {}
        for mapping in sql_doc_fields:
            fid = mapping['FieldID']
            if fid not in field_usage:
                field_usage[fid] = set()
            field_usage[fid].add(mapping['DocumentID'])
        
        # Analyze fields for this document
        unique_fields = set()
        for mapping in doc_field_mappings:
            field_id = mapping['FieldID']
            count = mapping.get('Count', 1)
            unique_fields.add(field_id)
            
            result['TotalFieldInstances'] += count
            
            # Determine category
            for category, field_ids in field_categories.items():
                if field_id in field_ids:
                    result[f'{category}_Count'] += count
                    
                    # Check if field is unique or reused
                    if len(field_usage.get(field_id, set())) == 1:
                        result[f'{category}_Unique'] += 1
                    else:
                        result[f'{category}_Reused'] += 1
                    break
        
        result['UniqueFields'] = len(unique_fields)
    
    linked_data.append(result)

# Create DataFrame
df_linked = pd.DataFrame(linked_data)

print(f"\nLinked {len(df_linked)} client requirements")
print(f"Documents with SQL data: {len(df_linked[df_linked['SQLDocumentID'].notna()])}")
print(f"Documents without SQL data: {len(df_linked[df_linked['SQLDocumentID'].isna()])}")

# Show statistics
docs_with_data = df_linked[df_linked['SQLDocumentID'].notna()]
if len(docs_with_data) > 0:
    print("\nField statistics for documents with SQL data:")
    print(f"  Average total field instances: {docs_with_data['TotalFieldInstances'].mean():.1f}")
    print(f"  Average unique fields: {docs_with_data['UniqueFields'].mean():.1f}")
    
    print("\nAverage by category:")
    for category in field_categories.keys():
        avg_count = docs_with_data[f'{category}_Count'].mean()
        if avg_count > 0:
            print(f"  {category}: {avg_count:.1f} instances")

# Save the corrected analysis
df_linked.to_excel('CORRECTED_linkage_analysis.xlsx', index=False)
print("\nSaved corrected analysis to CORRECTED_linkage_analysis.xlsx")

# Also save detailed statistics
stats = {
    'total_client_requirements': len(df_client),
    'sql_documents': len(sql_docs),
    'direct_matches': len(matches),
    'match_rate': f"{len(matches)/len(df_client)*100:.1f}%",
    'documents_with_field_data': len(docs_with_fields),
    'total_fields': len(sql_fields),
    'total_field_mappings': len(sql_doc_fields),
    'field_categories': {k: len(v) for k, v in field_categories.items()}
}

with open('CORRECTED_statistics.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("\nSaved statistics to CORRECTED_statistics.json")
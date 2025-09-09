import json
import pandas as pd
from pathlib import Path

# Load all SQL export files
sql_path = Path('../ImportantData/SQLExport')

# Load Documents
with open(sql_path / 'dbo_Documents.json', 'r') as f:
    docs_json = json.load(f)
    docs = docs_json.get('data', [])
    docs_metadata = docs_json.get('metadata', {})

print(f"Documents table:")
print(f"  Total documents: {len(docs)}")
if docs:
    print(f"  Fields: {list(docs[0].keys())}")
    print(f"  Sample records:")
    for doc in docs[:5]:
        print(f"    ID: {doc['DocumentID']}, Filename: {doc['Filename']}")

# Load Fields
with open(sql_path / 'dbo_Fields.json', 'r') as f:
    fields_json = json.load(f)
    fields = fields_json.get('data', [])
    fields_metadata = fields_json.get('metadata', {})

print(f"\nFields table:")
print(f"  Total fields: {len(fields)}")
if fields:
    print(f"  Columns: {list(fields[0].keys())}")
    # Group fields by category
    categories = {}
    for field in fields:
        cat = field.get('Category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    print(f"  Field categories:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count} fields")

# Load DocumentFields (the mapping table)
with open(sql_path / 'dbo_DocumentFields.json', 'r') as f:
    doc_fields_json = json.load(f)
    doc_fields = doc_fields_json.get('data', [])
    doc_fields_metadata = doc_fields_json.get('metadata', {})

print(f"\nDocumentFields table (mapping):")
print(f"  Total mappings: {len(doc_fields)}")
if doc_fields:
    print(f"  Columns: {list(doc_fields[0].keys())}")

# Load combined analysis
with open(sql_path / 'combined_analysis.json', 'r') as f:
    combined = json.load(f)
    
print(f"\nCombined analysis:")
if isinstance(combined, dict) and 'data' in combined:
    combined_data = combined['data']
    print(f"  Total records: {len(combined_data)}")
    if combined_data:
        print(f"  Fields: {list(combined_data[0].keys())}")
        # Show sample record
        sample = combined_data[0]
        print(f"  Sample record:")
        for key, value in sample.items():
            print(f"    {key}: {value}")

# Load export summary
with open(sql_path / 'export_summary.json', 'r') as f:
    summary = json.load(f)
    
print(f"\nExport summary:")
print(json.dumps(summary, indent=2)[:500])

# Extract document names from SQL data
sql_doc_names = set()
for doc in docs:
    filename = doc['Filename']
    # Remove extension to get the template name
    name = filename.replace('.dot', '').replace('.docx', '')
    sql_doc_names.add(name)

print(f"\nUnique document names in SQL: {len(sql_doc_names)}")
print(f"First 10 SQL document names: {list(sql_doc_names)[:10]}")

# Save for later processing
with open('sql_document_names.json', 'w') as f:
    json.dump(list(sql_doc_names), f, indent=2)
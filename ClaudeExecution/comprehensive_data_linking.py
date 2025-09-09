import xml.etree.ElementTree as ET
import json
import pandas as pd
import os
from pathlib import Path
from collections import defaultdict
import re

print("=" * 80)
print("COMPREHENSIVE DATA LINKING ANALYSIS")
print("=" * 80)

# 1. Load ClientRequirements Excel
print("\n1. Loading ClientRequirements.xlsx...")
excel_path = '../ImportantData/ClientRequirements.xlsx'
df_client = pd.read_excel(excel_path)
print(f"   Loaded {len(df_client)} rows from ClientRequirements")
print(f"   Unique titles: {df_client['Current Title'].nunique()}")

# 2. Load main manifest precedents
print("\n2. Loading ExportSandI.Manifest.xml...")
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

manifest_precedents = {}
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    # Extract PrecTitle from description
    prec_title = None
    desc_lines = description.split('\n')
    for i, line in enumerate(desc_lines):
        if i == 2:  # Third line usually contains the PrecTitle
            prec_title = line.strip()
            break
    
    manifest_precedents[code] = {
        'Code': code,
        'Name': name,
        'Description': description,
        'PrecTitle_from_desc': prec_title
    }

print(f"   Found {len(manifest_precedents)} precedent items")

# 3. Map precedent codes to subfolder manifests
print("\n3. Mapping precedent subfolders...")
precedents_path = Path('../ImportantData/ExportSandI/Precedents')
subfolder_data = {}
missing_manifests = []

for code in manifest_precedents:
    folder_path = precedents_path / code
    manifest_file = folder_path / 'manifest.xml'
    
    if manifest_file.exists():
        try:
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            
            # Find PRECEDENT element
            prec_elem = root.find('.//PRECEDENT')
            if prec_elem is not None:
                prec_title_elem = prec_elem.find('PrecTitle')
                prec_desc_elem = prec_elem.find('PrecDesc')
                prec_type_elem = prec_elem.find('PrecType')
                
                subfolder_data[code] = {
                    'PrecTitle': prec_title_elem.text if prec_title_elem is not None else None,
                    'PrecDesc': prec_desc_elem.text if prec_desc_elem is not None else None,
                    'PrecType': prec_type_elem.text if prec_type_elem is not None else None,
                    'manifest_exists': True
                }
        except Exception as e:
            print(f"   Error parsing {manifest_file}: {e}")
    else:
        missing_manifests.append(code)

print(f"   Successfully parsed {len(subfolder_data)} subfolder manifests")
print(f"   Missing manifests: {len(missing_manifests)}")

# 4. Load SQL Export data
print("\n4. Loading SQL Export data...")
sql_path = Path('../ImportantData/SQLExport')

# Load Documents
with open(sql_path / 'dbo_Documents.json', 'r') as f:
    docs_json = json.load(f)
    sql_docs = docs_json.get('data', [])

# Create lookup for SQL documents
sql_doc_lookup = {}
for doc in sql_docs:
    filename = doc['Filename']
    # Remove extension to get template name
    name = filename.replace('.dot', '').replace('.docx', '')
    sql_doc_lookup[name] = doc

print(f"   Loaded {len(sql_docs)} documents from SQL")

# Load Fields
with open(sql_path / 'dbo_Fields.json', 'r') as f:
    fields_json = json.load(f)
    sql_fields = fields_json.get('data', [])

print(f"   Loaded {len(sql_fields)} fields from SQL")

# Load DocumentFields (mapping)
with open(sql_path / 'dbo_DocumentFields.json', 'r') as f:
    doc_fields_json = json.load(f)
    sql_doc_fields = doc_fields_json.get('data', [])

print(f"   Loaded {len(sql_doc_fields)} document-field mappings")

# 5. Create comprehensive linking
print("\n5. Creating comprehensive data linkage...")

linked_data = []
unmatched_client_reqs = []
matched_client_reqs = []

for idx, row in df_client.iterrows():
    current_title = row['Current Title']
    description = row['Description']
    complexity = row['Complexity']
    
    # Initialize match data
    match_data = {
        'ClientReq_Title': current_title,
        'ClientReq_Description': description,
        'ClientReq_Complexity': complexity,
        'Manifest_Code': None,
        'Manifest_Name': None,
        'Subfolder_PrecTitle': None,
        'Subfolder_PrecDesc': None,
        'SQL_DocumentID': None,
        'SQL_Filename': None,
        'Field_Count': 0,
        'Match_Status': 'Not Found'
    }
    
    # Try to find matches
    # First, check if current_title matches any PrecTitle in subfolders
    for code, subfolder in subfolder_data.items():
        if subfolder.get('PrecTitle') == current_title:
            match_data['Manifest_Code'] = code
            match_data['Manifest_Name'] = manifest_precedents.get(code, {}).get('Name')
            match_data['Subfolder_PrecTitle'] = subfolder.get('PrecTitle')
            match_data['Subfolder_PrecDesc'] = subfolder.get('PrecDesc')
            match_data['Match_Status'] = 'Matched via PrecTitle'
            
            # Check SQL data
            if current_title in sql_doc_lookup:
                sql_doc = sql_doc_lookup[current_title]
                match_data['SQL_DocumentID'] = sql_doc['DocumentID']
                match_data['SQL_Filename'] = sql_doc['Filename']
                
                # Count fields for this document
                field_count = sum(1 for df in sql_doc_fields if df['DocumentID'] == sql_doc['DocumentID'])
                match_data['Field_Count'] = field_count
            break
    
    # If not found, try matching by manifest name
    if match_data['Match_Status'] == 'Not Found':
        for code, manifest in manifest_precedents.items():
            if manifest.get('Name', '').lower() == current_title.lower():
                match_data['Manifest_Code'] = code
                match_data['Manifest_Name'] = manifest.get('Name')
                match_data['Match_Status'] = 'Matched via Name'
                
                # Get subfolder data if exists
                if code in subfolder_data:
                    match_data['Subfolder_PrecTitle'] = subfolder_data[code].get('PrecTitle')
                    match_data['Subfolder_PrecDesc'] = subfolder_data[code].get('PrecDesc')
                break
    
    linked_data.append(match_data)
    
    if match_data['Match_Status'] != 'Not Found':
        matched_client_reqs.append(current_title)
    else:
        unmatched_client_reqs.append(current_title)

# 6. Generate statistics
print("\n6. LINKAGE STATISTICS:")
print(f"   Total Client Requirements: {len(df_client)}")
print(f"   Successfully matched: {len(matched_client_reqs)} ({len(matched_client_reqs)/len(df_client)*100:.1f}%)")
print(f"   Unmatched: {len(unmatched_client_reqs)} ({len(unmatched_client_reqs)/len(df_client)*100:.1f}%)")

# Count matches by type
match_types = defaultdict(int)
for item in linked_data:
    match_types[item['Match_Status']] += 1

print("\n   Match types:")
for status, count in match_types.items():
    print(f"     {status}: {count}")

# 7. Analyze field categories from SQL
print("\n7. Analyzing field categories...")

# Parse field codes to identify categories
field_categories = defaultdict(int)
for field in sql_fields:
    field_code = field.get('FieldCode', '')
    
    # Categorize based on field code patterns
    if 'IF' in field_code.upper():
        field_categories['IF Statements'] += 1
    elif 'DOCVARIABLE' in field_code:
        field_categories['Document Variables'] += 1
    elif 'MERGEFIELD' in field_code:
        field_categories['Merge Fields'] += 1
    elif 'INCLUDETEXT' in field_code:
        field_categories['Include Text'] += 1
    elif 'REF' in field_code:
        field_categories['References'] += 1
    else:
        field_categories['Other'] += 1

print("   Field categories found:")
for cat, count in sorted(field_categories.items()):
    print(f"     {cat}: {count}")

# 8. Save comprehensive results
print("\n8. Saving results...")

# Convert to DataFrame and save as Excel
df_linked = pd.DataFrame(linked_data)
df_linked.to_excel('linked_data_comprehensive.xlsx', index=False)
print("   Saved linked_data_comprehensive.xlsx")

# Save unmatched items
with open('unmatched_client_requirements.json', 'w') as f:
    json.dump(unmatched_client_reqs, f, indent=2)
print(f"   Saved {len(unmatched_client_reqs)} unmatched requirements")

# Save match statistics
stats = {
    'total_client_requirements': len(df_client),
    'matched': len(matched_client_reqs),
    'unmatched': len(unmatched_client_reqs),
    'match_rate': f"{len(matched_client_reqs)/len(df_client)*100:.1f}%",
    'match_types': dict(match_types),
    'field_categories': dict(field_categories),
    'manifest_precedents_count': len(manifest_precedents),
    'subfolder_manifests_parsed': len(subfolder_data),
    'sql_documents': len(sql_docs),
    'sql_fields': len(sql_fields),
    'sql_mappings': len(sql_doc_fields)
}

with open('linkage_statistics.json', 'w') as f:
    json.dump(stats, f, indent=2)
print("   Saved linkage_statistics.json")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
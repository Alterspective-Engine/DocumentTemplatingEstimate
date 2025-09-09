import xml.etree.ElementTree as ET
import pymssql
import pandas as pd
from pathlib import Path

print("=" * 80)
print("FINDING THE MAPPING BETWEEN CODES AND NAMES")
print("=" * 80)

# Load the main manifest to get the mapping
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

# Extract mapping from manifest
code_to_name_mapping = {}
name_to_code_mapping = {}

for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    # Extract PrecTitle from description (usually on third line)
    prec_title = None
    desc_lines = description.split('\n')
    for i, line in enumerate(desc_lines):
        if i == 2:  # Third line
            prec_title = line.strip()
            break
    
    if code and name:
        code_to_name_mapping[code] = {
            'Name': name,
            'PrecTitle': prec_title,
            'Description': description
        }
        
        # Also create reverse mapping
        if name:
            name_to_code_mapping[name.lower()] = code
        if prec_title:
            name_to_code_mapping[prec_title.lower()] = code

print(f"Found {len(code_to_name_mapping)} precedent mappings in manifest")

# Show some examples
print("\nSample mappings (Code -> Name/PrecTitle):")
for code, info in list(code_to_name_mapping.items())[:10]:
    print(f"  {code} -> Name: {info['Name']}, PrecTitle: {info['PrecTitle']}")

# Load Client Requirements
df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
print(f"\n\nClient Requirements: {len(df_client)} rows")

# Connect to database
server = 'mosmar-cip.database.windows.net'
database = 'Mosmar_CIP_Dev'
username = 'mosmaradmin'
password = 'M0sM4r.2021'

conn = pymssql.connect(
    server=server,
    user=username,
    password=password,
    database=database,
    tds_version='7.4'
)
cursor = conn.cursor()

# Get all documents from database
cursor.execute("SELECT DocumentID, Filename FROM dbo.Documents")
all_docs = cursor.fetchall()
print(f"SQL Documents: {len(all_docs)}")

# Try to match using the mapping
matches = []
no_matches_client = []
no_matches_sql = []

# For each client requirement, find its code and then check SQL
for idx, row in df_client.iterrows():
    title = row['Current Title']
    title_lower = title.lower()
    
    # Try to find the code for this title
    code = name_to_code_mapping.get(title_lower)
    
    if code:
        # Check if this code exists as a filename in SQL
        sql_filename = f"{code}.dot"
        sql_match = next((doc for doc in all_docs if doc[1] == sql_filename), None)
        
        if sql_match:
            matches.append({
                'ClientTitle': title,
                'Code': code,
                'SQLDocumentID': sql_match[0],
                'SQLFilename': sql_match[1]
            })
        else:
            # Also check without extension
            sql_match = next((doc for doc in all_docs if doc[1] == code), None)
            if sql_match:
                matches.append({
                    'ClientTitle': title,
                    'Code': code,
                    'SQLDocumentID': sql_match[0],
                    'SQLFilename': sql_match[1]
                })
            else:
                no_matches_sql.append({'ClientTitle': title, 'Code': code})
    else:
        no_matches_client.append(title)

print(f"\n" + "=" * 80)
print("MATCHING RESULTS USING MANIFEST MAPPING")
print("=" * 80)

print(f"Successfully matched: {len(matches)}")
print(f"Client titles without code mapping: {len(no_matches_client)}")
print(f"Codes not found in SQL: {len(no_matches_sql)}")

if matches:
    print(f"\nSample successful matches:")
    for match in matches[:10]:
        print(f"  {match['ClientTitle']} -> Code {match['Code']} -> SQL ID {match['SQLDocumentID']} ({match['SQLFilename']})")

if no_matches_client:
    print(f"\nSample client titles without code mapping:")
    for title in no_matches_client[:10]:
        print(f"  - {title}")

if no_matches_sql:
    print(f"\nSample codes not found in SQL:")
    for item in no_matches_sql[:10]:
        print(f"  {item['ClientTitle']} -> Code {item['Code']} (not in SQL)")

# Also check the reverse - what SQL documents match manifest codes
sql_matched = set()
for doc_id, filename in all_docs:
    if filename:
        basename = filename.replace('.dot', '').replace('.docx', '')
        if basename in code_to_name_mapping:
            sql_matched.add(basename)

print(f"\n\nSQL documents that match manifest codes: {len(sql_matched)}")

# Save the mapping for use in the comprehensive analysis
mapping_data = []
for idx, row in df_client.iterrows():
    title = row['Current Title']
    title_lower = title.lower()
    code = name_to_code_mapping.get(title_lower)
    
    mapping_data.append({
        'ClientTitle': title,
        'Description': row['Description'],
        'Complexity': row['Complexity'],
        'MappedCode': code,
        'HasCode': code is not None
    })

df_mapping = pd.DataFrame(mapping_data)
df_mapping.to_excel('client_to_code_mapping.xlsx', index=False)
print(f"\nSaved mapping to client_to_code_mapping.xlsx")

conn.close()

print("\n" + "=" * 80)
print("MAPPING ANALYSIS COMPLETE")
print("=" * 80)
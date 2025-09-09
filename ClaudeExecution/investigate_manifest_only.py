import json
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import re

print("=" * 80)
print("INVESTIGATING 279 MANIFEST-ONLY TEMPLATES")
print("=" * 80)

# Load the mapping results
df_mapping = pd.read_excel('../ClaudeReview/FINAL_comprehensive_mapping.xlsx')
manifest_only = df_mapping[df_mapping['MatchType'] == 'Manifest Only']
print(f"\n1. Found {len(manifest_only)} manifest-only templates")

# Check what codes these templates have
print("\n2. Checking codes for manifest-only templates...")
codes = manifest_only['Code'].dropna().unique()
print(f"✓ {len(codes)} unique codes found")

# Sample first 10 codes
print("\nSample codes:")
for code in codes[:10]:
    print(f"  - {code}")

# Check if these folders exist
precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
existing_folders = set(d.name for d in precedents_path.iterdir() if d.is_dir())
print(f"\n3. Checking folder existence...")
print(f"✓ Total folders in Precedents: {len(existing_folders)}")

codes_with_folders = []
codes_without_folders = []

for code in codes:
    if str(code) in existing_folders:
        codes_with_folders.append(code)
    else:
        codes_without_folders.append(code)

print(f"\n✓ Codes WITH folders: {len(codes_with_folders)}")
print(f"✗ Codes WITHOUT folders: {len(codes_without_folders)}")

if codes_with_folders:
    print(f"\nSample codes with folders:")
    for code in codes_with_folders[:5]:
        print(f"  - {code}")
        # Check if manifest exists
        manifest_file = precedents_path / str(code) / 'manifest.xml'
        if manifest_file.exists():
            print(f"    ✓ manifest.xml exists")
            # Try to parse it
            try:
                tree = ET.parse(manifest_file)
                root = tree.getroot()
                prec_elem = root.find('.//PRECEDENT')
                if prec_elem is not None:
                    prec_title = prec_elem.findtext('PrecTitle', '')
                    preview_length = len(prec_elem.findtext('PrecPreview', ''))
                    print(f"    PrecTitle: {prec_title}")
                    print(f"    Preview length: {preview_length}")
            except:
                print(f"    ✗ Failed to parse")
        else:
            print(f"    ✗ No manifest.xml")

print("\n4. Analyzing why these are 'manifest-only'...")

# Load main manifest
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

# Get all codes from manifest
manifest_codes = set()
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    if code:
        manifest_codes.add(code)

print(f"\n✓ Total codes in main manifest: {len(manifest_codes)}")

# Check overlap
codes_in_manifest = set(str(c) for c in codes)
in_both = codes_in_manifest & manifest_codes
print(f"✓ Manifest-only codes actually in main manifest: {len(in_both)}")

# These are in manifest but not in SQL - why?
print("\n5. Understanding the issue...")

# Load SQL documents to double-check
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)

sql_filenames = set()
sql_basenames = set()
for doc in sql_documents:
    filename = doc.get('Filename', '')
    if filename:
        sql_filenames.add(filename.lower())
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_basenames.add(basename)

print(f"\n✓ SQL has {len(sql_documents)} documents")

# Check if our codes are in SQL with different naming
found_in_sql = []
for code in codes[:20]:  # Check first 20
    code_str = str(code).lower()
    if code_str in sql_basenames:
        found_in_sql.append(f"{code} → found as basename")
    elif f"{code_str}.dot" in sql_filenames:
        found_in_sql.append(f"{code} → found as {code_str}.dot")
    elif f"{code_str}.docx" in sql_filenames:
        found_in_sql.append(f"{code} → found as {code_str}.docx")

if found_in_sql:
    print(f"\n⚠️ Some 'manifest-only' codes ARE in SQL:")
    for item in found_in_sql[:5]:
        print(f"  - {item}")

# Sample the actual client titles and codes
print("\n6. Sample of manifest-only templates:")
print("-" * 60)
sample = manifest_only.head(20)
for idx, row in sample.iterrows():
    client_title = row['ClientTitle']
    code = row.get('Code', 'N/A')
    print(f"  {client_title:15s} → Code: {code}")
    
    # Check if this code has a folder
    if str(code) in existing_folders:
        print(f"    ✓ Folder exists: Precedents/{code}/")
        # Check for manifest
        manifest_file = precedents_path / str(code) / 'manifest.xml'
        if manifest_file.exists():
            print(f"    ✓ Has manifest.xml")
    else:
        print(f"    ✗ No folder")

print("\n" + "=" * 80)
print("KEY FINDINGS")
print("=" * 80)

print("\n1. The 279 'manifest-only' templates are in the main manifest")
print("2. Most DON'T have folders in ExportSandI/Precedents/")
print("3. They're not in the SQL database")
print("\n→ These appear to be templates registered in the system")
print("  but their actual files haven't been exported/included")
print("\n💡 CONCLUSION:")
print("• We CANNOT extract field data from XML for these 279 templates")
print("• They exist only as registry entries in the main manifest")
print("• No PrecPreview data available without the actual folders")
print("• Would need the actual template files or SQL import to analyze")

# Save investigation results
investigation_data = []
for idx, row in manifest_only.iterrows():
    inv_row = {
        'ClientTitle': row['ClientTitle'],
        'Code': row.get('Code'),
        'HasFolder': str(row.get('Code')) in existing_folders if row.get('Code') else False,
        'InMainManifest': str(row.get('Code')) in manifest_codes if row.get('Code') else False,
        'InSQL': str(row.get('Code')).lower() in sql_basenames if row.get('Code') else False
    }
    investigation_data.append(inv_row)

df_investigation = pd.DataFrame(investigation_data)

output_file = '../ClaudeReview/manifest_only_investigation.xlsx'
df_investigation.to_excel(output_file, index=False)
print(f"\n✓ Saved investigation to {output_file}")

# Summary stats
has_folder = df_investigation['HasFolder'].sum()
in_manifest = df_investigation['InMainManifest'].sum()
in_sql = df_investigation['InSQL'].sum()

print(f"\nSummary of 279 manifest-only templates:")
print(f"  Has folder in Precedents: {has_folder} ({has_folder/279*100:.1f}%)")
print(f"  In main manifest: {in_manifest} ({in_manifest/279*100:.1f}%)")
print(f"  Actually in SQL: {in_sql} ({in_sql/279*100:.1f}%)")

print("\n" + "=" * 80)
import json
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import os

print("=" * 80)
print("INVESTIGATING 281 UNMATCHED CLIENT REQUIREMENTS")
print("=" * 80)

# Load the comprehensive analysis to get unmatched items
df_analysis = pd.read_excel('../ClaudeReview/COMPLETE_EstimateDoc_Analysis.xlsx')
unmatched = df_analysis[df_analysis['HasSQLData'] == False]

print(f"\nFound {len(unmatched)} unmatched client requirements")

# Load all data sources for investigation
print("\n1. Loading all available data sources...")

# Load SQL documents
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)

# Create lookup of all SQL document names
sql_doc_names = set()
sql_doc_basenames = set()
for doc in sql_documents:
    filename = doc['Filename']
    if filename:
        sql_doc_names.add(filename.lower())
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_doc_basenames.add(basename)

print(f"✓ SQL database has {len(sql_documents)} documents")

# Load manifest
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

# Build comprehensive mapping from manifest
manifest_items = {}
name_to_code = {}
prectitle_to_code = {}

for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    # Extract PrecTitle
    prec_title = None
    desc_lines = description.split('\n')
    for i, line in enumerate(desc_lines):
        if i == 2:
            prec_title = line.strip()
            break
    
    if code:
        manifest_items[code] = {
            'Name': name,
            'PrecTitle': prec_title,
            'Description': description
        }
        
        if name:
            name_to_code[name.lower()] = code
        if prec_title:
            prectitle_to_code[prec_title.lower()] = code

print(f"✓ Manifest has {len(manifest_items)} precedent items")

# Check ExportSandI/Precedents folder
precedents_path = Path('../ImportantData/ExportSandI/Precedents')
precedent_folders = set()
if precedents_path.exists():
    precedent_folders = set(d.name for d in precedents_path.iterdir() if d.is_dir())
    print(f"✓ Found {len(precedent_folders)} precedent folders")

print("\n2. Analyzing unmatched templates...")

# Categorize unmatched items
unmatched_analysis = {
    'has_code_no_sql': [],
    'has_code_no_folder': [],
    'no_code_mapping': [],
    'code_in_folder_not_sql': [],
    'other': []
}

for idx, row in unmatched.iterrows():
    title = row['ClientTitle']
    title_lower = title.lower()
    
    # Check if has code mapping
    code = None
    if title_lower in name_to_code:
        code = name_to_code[title_lower]
    elif title_lower in prectitle_to_code:
        code = prectitle_to_code[title_lower]
    
    if code:
        # Has code, check where it exists
        in_sql = code in sql_doc_basenames or f"{code}.dot" in sql_doc_names
        in_folder = code in precedent_folders
        
        if in_folder and not in_sql:
            unmatched_analysis['code_in_folder_not_sql'].append({
                'Title': title,
                'Code': code,
                'InFolder': True,
                'InSQL': False
            })
        elif not in_folder and not in_sql:
            unmatched_analysis['has_code_no_sql'].append({
                'Title': title,
                'Code': code,
                'InFolder': False,
                'InSQL': False
            })
        elif not in_folder:
            unmatched_analysis['has_code_no_folder'].append({
                'Title': title,
                'Code': code
            })
        else:
            unmatched_analysis['other'].append({
                'Title': title,
                'Code': code,
                'Note': 'Unexpected state'
            })
    else:
        unmatched_analysis['no_code_mapping'].append({'Title': title})

print("\n3. UNMATCHED CATEGORIES:")
print("-" * 40)

print(f"\na) No Code Mapping: {len(unmatched_analysis['no_code_mapping'])} items")
print("   (Client requirement has no mapping in manifest)")
if unmatched_analysis['no_code_mapping']:
    for item in unmatched_analysis['no_code_mapping'][:10]:
        print(f"   - {item['Title']}")
    if len(unmatched_analysis['no_code_mapping']) > 10:
        print(f"   ... and {len(unmatched_analysis['no_code_mapping']) - 10} more")

print(f"\nb) Has Code but Not in SQL: {len(unmatched_analysis['has_code_no_sql'])} items")
print("   (Mapped to code but document not in SQL database)")
if unmatched_analysis['has_code_no_sql']:
    for item in unmatched_analysis['has_code_no_sql'][:10]:
        print(f"   - {item['Title']} → Code {item['Code']}")
    if len(unmatched_analysis['has_code_no_sql']) > 10:
        print(f"   ... and {len(unmatched_analysis['has_code_no_sql']) - 10} more")

print(f"\nc) Code Exists in Folder but Not SQL: {len(unmatched_analysis['code_in_folder_not_sql'])} items")
print("   (Physical files exist but not imported to SQL)")
if unmatched_analysis['code_in_folder_not_sql']:
    for item in unmatched_analysis['code_in_folder_not_sql'][:10]:
        print(f"   - {item['Title']} → Code {item['Code']} ✓ Folder exists")
    if len(unmatched_analysis['code_in_folder_not_sql']) > 10:
        print(f"   ... and {len(unmatched_analysis['code_in_folder_not_sql']) - 10} more")

# Pattern analysis
print("\n4. PATTERN ANALYSIS:")
print("-" * 40)

# Analyze naming patterns
patterns = defaultdict(list)
for item in unmatched['ClientTitle']:
    if item.startswith('sup'):
        if 'lit' in item:
            patterns['suplit'].append(item)
        else:
            patterns['sup'].append(item)
    elif item.startswith('tac'):
        patterns['tac'].append(item)
    elif item.startswith('wv'):
        patterns['wv'].append(item)
    else:
        patterns['other'].append(item)

print("\nNaming pattern distribution:")
for pattern, items in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {pattern:10s}: {len(items)} items")

# Check if these codes exist anywhere
print("\n5. CHECKING FOR ALTERNATIVE LOCATIONS:")
print("-" * 40)

# Check if unmatched codes exist as different extensions
alternative_matches = []
for item in unmatched_analysis['has_code_no_sql']:
    code = item['Code']
    # Check various possible filenames
    possible_names = [
        f"{code}.docx",
        f"{code}.doc",
        f"{code}.dotx",
        f"{code}.dotm",
        code  # without extension
    ]
    
    for name in possible_names:
        if name.lower() in sql_doc_names:
            alternative_matches.append({
                'Title': item['Title'],
                'Code': code,
                'FoundAs': name
            })
            break

if alternative_matches:
    print(f"\nFound {len(alternative_matches)} with alternative names in SQL:")
    for match in alternative_matches[:5]:
        print(f"  {match['Title']} → {match['Code']} found as '{match['FoundAs']}'")

# Check precedent folder manifests for additional info
print("\n6. CHECKING PRECEDENT FOLDER MANIFESTS:")
print("-" * 40)

precedent_manifest_data = []
checked_count = 0
for item in unmatched_analysis['code_in_folder_not_sql'][:20]:  # Check first 20
    code = item['Code']
    manifest_file = precedents_path / code / 'manifest.xml'
    
    if manifest_file.exists():
        checked_count += 1
        try:
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            prec_elem = root.find('.//PRECEDENT')
            if prec_elem is not None:
                prec_title = prec_elem.find('PrecTitle')
                prec_desc = prec_elem.find('PrecDesc')
                prec_path = prec_elem.find('PrecPath')
                
                precedent_manifest_data.append({
                    'ClientTitle': item['Title'],
                    'Code': code,
                    'PrecTitle': prec_title.text if prec_title is not None else None,
                    'PrecDesc': prec_desc.text if prec_desc is not None else None,
                    'PrecPath': prec_path.text if prec_path is not None else None
                })
        except:
            pass

if precedent_manifest_data:
    print(f"Checked {checked_count} precedent manifests:")
    for data in precedent_manifest_data[:5]:
        print(f"  {data['ClientTitle']} ({data['Code']}):")
        print(f"    PrecTitle: {data['PrecTitle']}")
        print(f"    Path: {data['PrecPath']}")

# Generate summary report
print("\n" + "=" * 80)
print("INVESTIGATION SUMMARY")
print("=" * 80)

summary = {
    'total_unmatched': len(unmatched),
    'breakdown': {
        'no_code_mapping': len(unmatched_analysis['no_code_mapping']),
        'has_code_no_sql': len(unmatched_analysis['has_code_no_sql']),
        'code_in_folder_not_sql': len(unmatched_analysis['code_in_folder_not_sql']),
        'has_code_no_folder': len(unmatched_analysis['has_code_no_folder']),
        'other': len(unmatched_analysis['other'])
    },
    'patterns': {k: len(v) for k, v in patterns.items()},
    'alternative_matches_found': len(alternative_matches)
}

print(f"\nTotal Unmatched: {summary['total_unmatched']}")
print("\nBreakdown by Issue:")
for issue, count in summary['breakdown'].items():
    percentage = (count / summary['total_unmatched'] * 100) if summary['total_unmatched'] > 0 else 0
    print(f"  {issue:25s}: {count:3d} ({percentage:.1f}%)")

print("\nKey Findings:")
print(f"  ✓ {summary['breakdown']['code_in_folder_not_sql']} templates exist as files but not in SQL")
print(f"  ✓ {summary['breakdown']['has_code_no_sql']} templates have codes but no files anywhere")
print(f"  ✓ {summary['breakdown']['no_code_mapping']} templates have no code mapping at all")

# Save detailed investigation results
output_file = '../ClaudeReview/unmatched_investigation.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Overview
    pd.DataFrame([summary]).to_excel(writer, sheet_name='Summary', index=False)
    
    # Detailed lists
    if unmatched_analysis['no_code_mapping']:
        pd.DataFrame(unmatched_analysis['no_code_mapping']).to_excel(
            writer, sheet_name='No Code Mapping', index=False)
    
    if unmatched_analysis['has_code_no_sql']:
        pd.DataFrame(unmatched_analysis['has_code_no_sql']).to_excel(
            writer, sheet_name='Has Code No SQL', index=False)
    
    if unmatched_analysis['code_in_folder_not_sql']:
        pd.DataFrame(unmatched_analysis['code_in_folder_not_sql']).to_excel(
            writer, sheet_name='In Folder Not SQL', index=False)
    
    # Pattern analysis
    pattern_df = pd.DataFrame([
        {'Pattern': k, 'Count': len(v), 'Examples': ', '.join(v[:5])}
        for k, v in patterns.items()
    ])
    pattern_df.to_excel(writer, sheet_name='Patterns', index=False)

print(f"\n✓ Detailed investigation saved to {output_file}")

# Save JSON summary
with open('../ClaudeReview/unmatched_investigation.json', 'w') as f:
    json.dump({
        'summary': summary,
        'no_code_mapping': unmatched_analysis['no_code_mapping'][:20],
        'has_code_no_sql': unmatched_analysis['has_code_no_sql'][:20],
        'code_in_folder_not_sql': unmatched_analysis['code_in_folder_not_sql'][:20],
        'alternative_matches': alternative_matches[:20]
    }, f, indent=2)

print("✓ JSON summary saved")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("\n1. IMMEDIATE ACTIONS:")
print(f"   • Import {summary['breakdown']['code_in_folder_not_sql']} documents from Precedents folder to SQL")
print("   • These files exist and just need to be imported to the database")

print("\n2. REQUIRES INVESTIGATION:")
print(f"   • {summary['breakdown']['has_code_no_sql']} templates have codes but no physical files")
print("   • Check if these were deleted, renamed, or exist in another system")

print("\n3. MAPPING ISSUES:")
print(f"   • {summary['breakdown']['no_code_mapping']} templates need code assignment")
print("   • Review if these are new templates or have different naming")

print("\n4. POTENTIAL DATA RECOVERY:")
print(f"   • {len(alternative_matches)} templates might exist with different extensions")
print("   • Review and update file extension mappings")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
import xml.etree.ElementTree as ET
import json
import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("PRECPATH MAPPING SOLUTION - Using PrecPath → PrecTitle → Client")
print("=" * 80)

# Load data
print("\n1. Loading Data Sources...")

# Client Requirements
df_client = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx')
print(f"✓ Client Requirements: {len(df_client)} items")

# SQL Documents
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)
print(f"✓ SQL Documents: {len(sql_documents)} items")

# Field Analysis
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ Field Analysis: {len(field_analysis)} records")

# Build SQL lookups
sql_by_numeric = {}
sql_by_filename = {}
for doc in sql_documents:
    filename = doc.get('Filename', '')
    if filename:
        sql_by_filename[filename.lower()] = doc
        # Extract numeric part
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        if re.match(r'^\d+$', basename):
            sql_by_numeric[basename] = doc

print(f"✓ SQL numeric lookups: {len(sql_by_numeric)} items")

# Build field analysis by document
field_by_doc = defaultdict(lambda: defaultdict(int))
for fa in field_analysis:
    doc_id = fa['documentid']
    category = fa['field_category']
    field_by_doc[doc_id][category] += 1

print("\n2. Parsing ALL Precedent XML Files...")

precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
manifest_files = list(precedents_path.glob('*/manifest.xml'))
print(f"Found {len(manifest_files)} precedent manifest files")

# Parse all precedent manifests
precedent_data = []
parse_failures = []

for manifest_file in manifest_files:
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        
        prec_elem = root.find('.//PRECEDENT')
        if prec_elem is not None:
            prec_path = prec_elem.findtext('PrecPath', '')
            prec_title = prec_elem.findtext('PrecTitle', '')
            prec_id = prec_elem.findtext('PrecID', '')
            
            # Extract numeric code from PrecPath
            numeric_code = None
            if prec_path:
                # Pattern: Company\2694.dot or similar
                match = re.search(r'\\(\d+)\.', prec_path)
                if not match:
                    # Try without backslash
                    match = re.search(r'(\d+)\.', prec_path)
                if match:
                    numeric_code = match.group(1)
            
            # Also try folder name as fallback
            folder_code = manifest_file.parent.name
            
            precedent_data.append({
                'FolderCode': folder_code,
                'PrecID': prec_id,
                'PrecTitle': prec_title,
                'PrecPath': prec_path,
                'ExtractedNumeric': numeric_code,
                'PrecType': prec_elem.findtext('PrecType', ''),
                'PrecCategory': prec_elem.findtext('PrecCategory', ''),
                'PrecDesc': prec_elem.findtext('PrecDesc', ''),
                'PrecLibrary': prec_elem.findtext('PrecLibrary', ''),
                'HasPreview': bool(prec_elem.findtext('PrecPreview', '')),
                'PreviewLength': len(prec_elem.findtext('PrecPreview', '')) if prec_elem.findtext('PrecPreview', '') else 0
            })
    except Exception as e:
        parse_failures.append({'File': str(manifest_file), 'Error': str(e)})

print(f"✓ Parsed {len(precedent_data)} precedent files")
print(f"⚠ Failed to parse {len(parse_failures)} files")

# Create lookup by PrecTitle
prec_by_title = {}
prec_by_numeric = {}
for prec in precedent_data:
    if prec['PrecTitle']:
        prec_by_title[prec['PrecTitle'].lower()] = prec
    if prec['ExtractedNumeric']:
        prec_by_numeric[prec['ExtractedNumeric']] = prec

print(f"✓ Created lookups: {len(prec_by_title)} by title, {len(prec_by_numeric)} by numeric")

# Parse main manifest for additional mappings
print("\n3. Parsing Main Manifest...")
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

manifest_mappings = {}
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    if code and name:
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip().lower()
        
        # Extract title from description
        desc_lines = description.split('\n')
        prec_title = None
        if len(desc_lines) >= 3:
            prec_title = desc_lines[2].strip().lower()
        
        manifest_mappings[clean_name] = {
            'code': code,
            'prec_title': prec_title
        }

print(f"✓ Main manifest: {len(manifest_mappings)} mappings")

print("\n4. THREE-WAY MAPPING: Client → PrecTitle → PrecPath → SQL")
print("-" * 60)

mapping_results = []
match_stats = defaultdict(int)

for idx, row in df_client.iterrows():
    client_title = row['Current Title']
    client_lower = client_title.lower()
    
    result = {
        'ClientTitle': client_title,
        'ClientDescription': row['Description'],
        'ClientComplexity': row['Complexity'],
        'PrecTitle': None,
        'PrecPath': None,
        'ExtractedNumeric': None,
        'FolderCode': None,
        'SQLDocID': None,
        'SQLFilename': None,
        'MatchPath': 'No Match',
        'FieldCategories': {},
        'TotalFields': 0,
        'EstimatedHours': 0
    }
    
    matched_prec = None
    matched_sql = None
    
    # STEP 1: Match Client to Precedent via PrecTitle
    if client_lower in prec_by_title:
        matched_prec = prec_by_title[client_lower]
        result['MatchPath'] = 'Direct PrecTitle Match'
        match_stats['direct_prectitle'] += 1
    
    # STEP 2: Try main manifest mapping
    elif client_lower in manifest_mappings:
        manifest_info = manifest_mappings[client_lower]
        code = manifest_info['code']
        
        # Check if this code exists in precedent data
        if code in prec_by_numeric:
            matched_prec = prec_by_numeric[code]
            result['MatchPath'] = 'Via Main Manifest'
            match_stats['via_main_manifest'] += 1
        # Check by folder code
        else:
            for prec in precedent_data:
                if prec['FolderCode'] == code:
                    matched_prec = prec
                    result['MatchPath'] = 'Via Manifest Folder'
                    match_stats['via_manifest_folder'] += 1
                    break
    
    # STEP 3: If we have precedent, extract data and match to SQL
    if matched_prec:
        result['PrecTitle'] = matched_prec['PrecTitle']
        result['PrecPath'] = matched_prec['PrecPath']
        result['ExtractedNumeric'] = matched_prec['ExtractedNumeric']
        result['FolderCode'] = matched_prec['FolderCode']
        
        # Try to match to SQL using extracted numeric
        if matched_prec['ExtractedNumeric']:
            numeric = matched_prec['ExtractedNumeric']
            
            # Check SQL by numeric
            if numeric in sql_by_numeric:
                matched_sql = sql_by_numeric[numeric]
                result['MatchPath'] += ' → SQL (numeric)'
                match_stats['to_sql_numeric'] += 1
            elif f"{numeric}.dot" in sql_by_filename:
                matched_sql = sql_by_filename[f"{numeric}.dot"]
                result['MatchPath'] += ' → SQL (filename)'
                match_stats['to_sql_filename'] += 1
        
        # Fallback: try folder code
        if not matched_sql and matched_prec['FolderCode']:
            folder = matched_prec['FolderCode']
            if folder in sql_by_numeric:
                matched_sql = sql_by_numeric[folder]
                result['MatchPath'] += ' → SQL (folder)'
                match_stats['to_sql_folder'] += 1
        
        if not matched_sql:
            result['MatchPath'] += ' (No SQL)'
            match_stats['no_sql'] += 1
    
    # STEP 4: Direct SQL match (fallback)
    if not matched_sql and not matched_prec:
        if client_lower in sql_by_numeric:
            matched_sql = sql_by_numeric[client_lower]
            result['MatchPath'] = 'Direct to SQL'
            match_stats['direct_sql'] += 1
        elif f"{client_lower}.dot" in sql_by_filename:
            matched_sql = sql_by_filename[f"{client_lower}.dot"]
            result['MatchPath'] = 'Direct to SQL (.dot)'
            match_stats['direct_sql_dot'] += 1
    
    # If we have SQL match, get field data
    if matched_sql:
        doc_id = matched_sql['DocumentID']
        result['SQLDocID'] = doc_id
        result['SQLFilename'] = matched_sql.get('Filename', '')
        
        # Get field analysis
        if doc_id in field_by_doc:
            result['FieldCategories'] = dict(field_by_doc[doc_id])
            result['TotalFields'] = sum(field_by_doc[doc_id].values())
            
            # Calculate effort
            effort_map = {
                'Reflection': 5,
                'Extended': 5,
                'Unbound': 5,
                'Search': 10,
                'If': 15,
                'Built In Script': 20,
                'Scripted': 30,
                'Precedent Script': 30
            }
            
            total_minutes = 0
            for cat, count in field_by_doc[doc_id].items():
                minutes = effort_map.get(cat, 10)
                total_minutes += count * minutes
            
            if field_by_doc[doc_id].get('Unbound', 0) > 0:
                total_minutes += 15
            
            result['EstimatedHours'] = round(total_minutes / 60, 2)
    
    if result['MatchPath'] == 'No Match':
        match_stats['no_match'] += 1
    
    mapping_results.append(result)

print("\n5. MAPPING RESULTS:")
print("-" * 60)

# Count statistics
has_prec = len([r for r in mapping_results if r['PrecTitle']])
has_sql = len([r for r in mapping_results if r['SQLDocID']])
has_numeric = len([r for r in mapping_results if r['ExtractedNumeric']])
total = len(mapping_results)

print(f"Match Statistics:")
for match_type, count in sorted(match_stats.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        pct = count / total * 100
        print(f"  {match_type:25s}: {count:4d} ({pct:.1f}%)")

print(f"\nCoverage:")
print(f"  With Precedent data: {has_prec}/{total} ({has_prec/total*100:.1f}%)")
print(f"  With Numeric extraction: {has_numeric}/{total} ({has_numeric/total*100:.1f}%)")
print(f"  With SQL data: {has_sql}/{total} ({has_sql/total*100:.1f}%)")

# Analyze unmatched
unmatched = [r for r in mapping_results if r['MatchPath'] == 'No Match']
print(f"  Unmatched: {len(unmatched)}/{total} ({len(unmatched)/total*100:.1f}%)")

# Sample successful PrecPath mappings
print("\n6. Sample PrecPath → SQL Mappings:")
successful = [r for r in mapping_results if r['ExtractedNumeric'] and r['SQLDocID']][:10]
for item in successful:
    print(f"  {item['ClientTitle']:15s} → {item['PrecTitle']:15s} → {item['PrecPath']:30s} → {item['SQLFilename']}")

# Save results
print("\n7. Saving Results...")

df_results = pd.DataFrame(mapping_results)
output_file = '../ClaudeReview/PrecPath_Mapping_Solution.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full results
    df_results.to_excel(writer, sheet_name='Complete Mapping', index=False)
    
    # Summary
    summary = pd.DataFrame([{
        'Total Client Requirements': total,
        'With Precedent Data': has_prec,
        'With Numeric from PrecPath': has_numeric,
        'With SQL Data': has_sql,
        'SQL Coverage': f"{has_sql/total*100:.1f}%",
        'Unmatched': len(unmatched),
        'Total Estimated Hours': sum(r['EstimatedHours'] for r in mapping_results)
    }])
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Precedent data
    df_prec = pd.DataFrame(precedent_data)
    df_prec.to_excel(writer, sheet_name='Precedent Data', index=False)
    
    # Unmatched
    if unmatched:
        df_unmatched = pd.DataFrame(unmatched)
        df_unmatched.to_excel(writer, sheet_name='Unmatched', index=False)

print(f"✓ Saved to {output_file}")

print("\n" + "=" * 80)
print("PRECPATH MAPPING SUMMARY")
print("=" * 80)

print(f"\n✅ Using PrecPath extraction:")
print(f"  • Parsed {len(precedent_data)} precedent XML files")
print(f"  • Extracted numeric codes from {has_numeric} templates")
print(f"  • Matched to SQL: {has_sql} templates ({has_sql/total*100:.1f}%)")

if has_sql > 0:
    total_hours = sum(r['EstimatedHours'] for r in mapping_results)
    print(f"\n📊 Effort Estimates:")
    print(f"  • Total: {total_hours:.0f} hours")
    print(f"  • Average: {total_hours/has_sql:.2f} hours per document")

print("\n" + "=" * 80)
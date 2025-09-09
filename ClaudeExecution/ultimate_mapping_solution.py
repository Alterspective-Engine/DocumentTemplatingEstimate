import xml.etree.ElementTree as ET
import json
import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("ULTIMATE MAPPING SOLUTION - COMBINING ALL APPROACHES")
print("=" * 80)

# Load all data sources
print("\n1. Loading All Data Sources...")

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
sql_by_basename = {}
for doc in sql_documents:
    filename = doc.get('Filename', '')
    if filename:
        sql_by_filename[filename.lower()] = doc
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_by_basename[basename] = doc
        
        # Extract pure numeric
        if re.match(r'^\d+$', basename):
            sql_by_numeric[basename] = doc

print(f"✓ SQL lookups: {len(sql_by_numeric)} numeric, {len(sql_by_basename)} basenames")

# Build field analysis by document
field_by_doc = defaultdict(lambda: defaultdict(int))
for fa in field_analysis:
    doc_id = fa['documentid']
    category = fa['field_category']
    field_by_doc[doc_id][category] += 1

# Parse Main Manifest first
print("\n2. Parsing Main Manifest (ExportSandI.Manifest.xml)...")
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

manifest_by_name = {}
manifest_by_code = {}

for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    if code and name:
        # Clean name
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip()
        
        # Extract title from description
        desc_lines = description.split('\n')
        prec_title = None
        if len(desc_lines) >= 3:
            prec_title = desc_lines[2].strip()
        
        info = {
            'code': code,
            'name': clean_name,
            'prec_title': prec_title,
            'description': description
        }
        
        manifest_by_name[clean_name.lower()] = info
        manifest_by_code[code] = info
        
        # Also index by prec_title if available
        if prec_title:
            manifest_by_name[prec_title.lower()] = info

print(f"✓ Main manifest: {len(manifest_by_code)} codes, {len(manifest_by_name)} names")

# Parse Precedent XMLs (with better error handling)
print("\n3. Parsing Precedent XML Files...")
precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
precedent_folders = list(precedents_path.iterdir()) if precedents_path.exists() else []
print(f"Found {len(precedent_folders)} precedent folders")

prec_by_folder = {}
prec_by_title = {}
prec_by_numeric = {}

for folder in precedent_folders:
    if folder.is_dir():
        manifest_file = folder / 'manifest.xml'
        if manifest_file.exists():
            try:
                tree = ET.parse(manifest_file)
                root = tree.getroot()
                
                prec_elem = root.find('.//PRECEDENT')
                if prec_elem is not None:
                    prec_data = {
                        'folder_code': folder.name,
                        'prec_id': prec_elem.findtext('PrecID', ''),
                        'prec_title': prec_elem.findtext('PrecTitle', ''),
                        'prec_path': prec_elem.findtext('PrecPath', ''),
                        'prec_type': prec_elem.findtext('PrecType', ''),
                        'prec_category': prec_elem.findtext('PrecCategory', ''),
                        'numeric_from_path': None
                    }
                    
                    # Extract numeric from PrecPath
                    if prec_data['prec_path']:
                        match = re.search(r'\\(\d+)\.', prec_data['prec_path'])
                        if not match:
                            match = re.search(r'(\d+)\.', prec_data['prec_path'])
                        if match:
                            prec_data['numeric_from_path'] = match.group(1)
                    
                    # Store in lookups
                    prec_by_folder[folder.name] = prec_data
                    
                    if prec_data['prec_title']:
                        prec_by_title[prec_data['prec_title'].lower()] = prec_data
                    
                    if prec_data['numeric_from_path']:
                        prec_by_numeric[prec_data['numeric_from_path']] = prec_data
            except:
                pass  # Skip failed parses

print(f"✓ Parsed {len(prec_by_folder)} precedent XMLs")
print(f"✓ Lookups: {len(prec_by_title)} by title, {len(prec_by_numeric)} by numeric")

# COMPREHENSIVE MAPPING
print("\n4. COMPREHENSIVE MAPPING - ALL STRATEGIES")
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
        'ManifestCode': None,
        'PrecTitle': None,
        'PrecPath': None,
        'NumericCode': None,
        'SQLDocID': None,
        'SQLFilename': None,
        'MatchStrategy': 'No Match',
        'FieldCategories': {},
        'TotalFields': 0,
        'EstimatedHours': 0
    }
    
    matched_sql = None
    numeric_code = None
    
    # STRATEGY 1: Direct SQL match
    if client_lower in sql_by_basename:
        matched_sql = sql_by_basename[client_lower]
        result['MatchStrategy'] = '1. Direct SQL'
        match_stats['1_direct_sql'] += 1
    elif f"{client_lower}.dot" in sql_by_filename:
        matched_sql = sql_by_filename[f"{client_lower}.dot"]
        result['MatchStrategy'] = '1. Direct SQL (.dot)'
        match_stats['1_direct_sql_dot'] += 1
    
    # STRATEGY 2: Via Precedent XML (PrecTitle → PrecPath → SQL)
    if not matched_sql and client_lower in prec_by_title:
        prec_data = prec_by_title[client_lower]
        result['PrecTitle'] = prec_data['prec_title']
        result['PrecPath'] = prec_data['prec_path']
        
        if prec_data['numeric_from_path']:
            numeric_code = prec_data['numeric_from_path']
            result['NumericCode'] = numeric_code
            
            if numeric_code in sql_by_numeric:
                matched_sql = sql_by_numeric[numeric_code]
                result['MatchStrategy'] = '2. PrecTitle→PrecPath→SQL'
                match_stats['2_prec_path_sql'] += 1
            else:
                result['MatchStrategy'] = '2. PrecTitle→PrecPath (no SQL)'
                match_stats['2_prec_path_no_sql'] += 1
    
    # STRATEGY 3: Via Main Manifest (Client → Manifest → SQL)
    if not matched_sql and client_lower in manifest_by_name:
        manifest_info = manifest_by_name[client_lower]
        code = manifest_info['code']
        result['ManifestCode'] = code
        
        # Try code as numeric in SQL
        if code in sql_by_numeric:
            matched_sql = sql_by_numeric[code]
            result['MatchStrategy'] = '3. Manifest→SQL (numeric)'
            match_stats['3_manifest_sql_numeric'] += 1
        elif f"{code}.dot" in sql_by_filename:
            matched_sql = sql_by_filename[f"{code}.dot"]
            result['MatchStrategy'] = '3. Manifest→SQL (.dot)'
            match_stats['3_manifest_sql_dot'] += 1
        # Try code in precedent folders
        elif code in prec_by_folder:
            prec_data = prec_by_folder[code]
            result['PrecTitle'] = prec_data['prec_title']
            result['PrecPath'] = prec_data['prec_path']
            
            if prec_data['numeric_from_path']:
                numeric_code = prec_data['numeric_from_path']
                result['NumericCode'] = numeric_code
                
                if numeric_code in sql_by_numeric:
                    matched_sql = sql_by_numeric[numeric_code]
                    result['MatchStrategy'] = '3. Manifest→Prec→SQL'
                    match_stats['3_manifest_prec_sql'] += 1
                else:
                    result['MatchStrategy'] = '3. Manifest→Prec (no SQL)'
                    match_stats['3_manifest_prec_no_sql'] += 1
            else:
                result['MatchStrategy'] = '3. Manifest only'
                match_stats['3_manifest_only'] += 1
        else:
            result['MatchStrategy'] = '3. Manifest only'
            match_stats['3_manifest_only'] += 1
    
    # STRATEGY 4: Extract numbers from client title
    if not matched_sql:
        numbers = re.findall(r'\d+', client_title)
        for num in numbers:
            if num in sql_by_numeric:
                matched_sql = sql_by_numeric[num]
                result['NumericCode'] = num
                result['MatchStrategy'] = '4. Numeric extraction'
                match_stats['4_numeric_extraction'] += 1
                break
    
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
    
    if result['MatchStrategy'] == 'No Match':
        match_stats['no_match'] += 1
    
    mapping_results.append(result)

# Calculate final statistics
print("\n5. FINAL RESULTS:")
print("-" * 60)

total = len(mapping_results)
has_sql = len([r for r in mapping_results if r['SQLDocID']])
has_manifest = len([r for r in mapping_results if r['ManifestCode']])
has_prec = len([r for r in mapping_results if r['PrecTitle']])
has_numeric = len([r for r in mapping_results if r['NumericCode']])
no_match = match_stats['no_match']

print("Match Strategy Breakdown:")
for strategy, count in sorted(match_stats.items()):
    pct = count / total * 100
    print(f"  {strategy:30s}: {count:4d} ({pct:.1f}%)")

print(f"\nOverall Coverage:")
print(f"  With SQL data: {has_sql}/{total} ({has_sql/total*100:.1f}%)")
print(f"  With Manifest code: {has_manifest}/{total} ({has_manifest/total*100:.1f}%)")
print(f"  With Precedent data: {has_prec}/{total} ({has_prec/total*100:.1f}%)")
print(f"  With Numeric code: {has_numeric}/{total} ({has_numeric/total*100:.1f}%)")
print(f"  No match: {no_match}/{total} ({no_match/total*100:.1f}%)")

# Effort statistics
if has_sql > 0:
    total_hours = sum(r['EstimatedHours'] for r in mapping_results)
    avg_hours = total_hours / has_sql
    print(f"\nEffort Estimates:")
    print(f"  Total: {total_hours:.0f} hours")
    print(f"  Average: {avg_hours:.2f} hours per document")

# Save comprehensive results
print("\n6. Saving Results...")

df_results = pd.DataFrame(mapping_results)
output_file = '../ClaudeReview/ULTIMATE_Mapping_Solution.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main results
    df_results.to_excel(writer, sheet_name='Complete Mapping', index=False)
    
    # Summary
    summary = pd.DataFrame([{
        'Total Client Requirements': total,
        'With SQL Data': has_sql,
        'SQL Coverage %': f"{has_sql/total*100:.1f}%",
        'With Manifest Code': has_manifest,
        'With Precedent Data': has_prec,
        'With Numeric Code': has_numeric,
        'No Match': no_match,
        'Total Estimated Hours': sum(r['EstimatedHours'] for r in mapping_results)
    }])
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Strategy breakdown
    strategy_df = pd.DataFrame(list(match_stats.items()), columns=['Strategy', 'Count'])
    strategy_df['Percentage'] = (strategy_df['Count'] / total * 100).round(1)
    strategy_df.sort_values('Count', ascending=False, inplace=True)
    strategy_df.to_excel(writer, sheet_name='Strategy Breakdown', index=False)
    
    # Unmatched
    unmatched = df_results[df_results['MatchStrategy'] == 'No Match']
    if len(unmatched) > 0:
        unmatched.to_excel(writer, sheet_name='Unmatched', index=False)

print(f"✓ Saved to {output_file}")

print("\n" + "=" * 80)
print("ULTIMATE MAPPING SOLUTION - FINAL SUMMARY")
print("=" * 80)

print(f"\n✅ BEST ACHIEVABLE RESULTS:")
print(f"  • SQL Coverage: {has_sql}/{total} ({has_sql/total*100:.1f}%)")
print(f"  • Total Mapping: {total - no_match}/{total} ({(total - no_match)/total*100:.1f}%)")

if has_sql > 0:
    print(f"\n📊 Based on SQL data:")
    print(f"  • {has_sql} templates with field analysis")
    print(f"  • {total_hours:.0f} total hours estimated")
    print(f"  • {avg_hours:.2f} average hours per template")

print("\n💡 KEY INSIGHT:")
print("  PrecPath extraction provides the critical link between")
print("  client names (sup059) and SQL numeric files (2694.dot)")

print("\n" + "=" * 80)
import json
import pandas as pd
import xml.etree.ElementTree as ET
import re
from collections import defaultdict
from pathlib import Path

print("=" * 80)
print("FINAL MAPPING SOLUTION - BRIDGING CLIENT → MANIFEST → SQL")
print("=" * 80)

# Load all data
print("\n1. Loading all data sources...")

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

# Parse Main Manifest
print("\n2. Parsing ExportSandI.Manifest.xml...")
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

# Build comprehensive mapping from manifest
name_to_code = {}
code_to_name = {}
code_to_info = {}

for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    if code and name:
        # Clean name (remove version markers)
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip()
        
        # Extract title from description (line 3)
        desc_lines = description.split('\n')
        prec_title = None
        if len(desc_lines) >= 3:
            prec_title = desc_lines[2].strip()
        
        # Store mappings
        name_to_code[clean_name.lower()] = code
        code_to_name[code] = clean_name
        
        code_to_info[code] = {
            'name': clean_name,
            'prec_title': prec_title,
            'description': description
        }
        
        # Also map by prec_title if available
        if prec_title:
            name_to_code[prec_title.lower()] = code

print(f"✓ Found {len(code_to_name)} code mappings in manifest")

# Build SQL lookups
print("\n3. Building SQL document lookups...")
sql_by_filename = {}
sql_by_basename = {}
sql_by_numeric = {}

for doc in sql_documents:
    filename = doc.get('Filename', '')
    if filename:
        # By filename
        sql_by_filename[filename.lower()] = doc
        
        # By basename
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_by_basename[basename] = doc
        
        # Extract numeric part
        if re.match(r'^\d+', basename):
            numeric = re.match(r'^(\d+)', basename).group(1)
            sql_by_numeric[numeric] = doc

print(f"✓ Built lookups: {len(sql_by_numeric)} numeric codes")

# Build field analysis by document
field_by_doc = defaultdict(lambda: defaultdict(int))
for fa in field_analysis:
    doc_id = fa['documentid']
    category = fa['field_category']
    field_by_doc[doc_id][category] += 1

print("\n4. THREE-STEP MAPPING: Client → Manifest → SQL")
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
        'SQLDocID': None,
        'SQLFilename': None,
        'MatchPath': 'No Match',
        'FieldCategories': {},
        'TotalFields': 0,
        'EstimatedHours': 0
    }
    
    matched_sql = None
    manifest_code = None
    
    # STEP 1: Client → SQL (Direct)
    if client_lower in sql_by_basename:
        matched_sql = sql_by_basename[client_lower]
        result['MatchPath'] = 'Direct to SQL'
        match_stats['direct_sql'] += 1
    elif f"{client_lower}.dot" in sql_by_filename:
        matched_sql = sql_by_filename[f"{client_lower}.dot"]
        result['MatchPath'] = 'Direct to SQL (.dot)'
        match_stats['direct_sql_dot'] += 1
    
    # STEP 2: Client → Manifest → SQL
    if not matched_sql:
        # Find manifest code
        if client_lower in name_to_code:
            manifest_code = name_to_code[client_lower]
            result['ManifestCode'] = manifest_code
            
            # Try to match code to SQL
            # Check if code is numeric and matches SQL
            if manifest_code in sql_by_numeric:
                matched_sql = sql_by_numeric[manifest_code]
                result['MatchPath'] = 'Client→Manifest→SQL (numeric)'
                match_stats['via_manifest_numeric'] += 1
            elif manifest_code in sql_by_basename:
                matched_sql = sql_by_basename[manifest_code]
                result['MatchPath'] = 'Client→Manifest→SQL (basename)'
                match_stats['via_manifest_basename'] += 1
            elif f"{manifest_code}.dot" in sql_by_filename:
                matched_sql = sql_by_filename[f"{manifest_code}.dot"]
                result['MatchPath'] = 'Client→Manifest→SQL (.dot)'
                match_stats['via_manifest_dot'] += 1
            else:
                result['MatchPath'] = 'Manifest Only (no SQL)'
                match_stats['manifest_only'] += 1
    
    # STEP 3: If still no match, try alternative approaches
    if not matched_sql and not manifest_code:
        # Extract numbers from client title
        client_numbers = re.findall(r'\d+', client_title)
        for num in client_numbers:
            if num in sql_by_numeric:
                # Check if it's a reasonable match
                sql_doc = sql_by_numeric[num]
                sql_name = sql_doc.get('Filename', '').lower()
                
                # Verify it's not a false positive
                if 'sup' in client_lower and ('sup' in sql_name or int(num) > 1000):
                    matched_sql = sql_doc
                    result['MatchPath'] = 'Numeric extraction match'
                    match_stats['numeric_extraction'] += 1
                    break
    
    # If we have SQL match, get field data
    if matched_sql:
        doc_id = matched_sql['DocumentID']
        result['SQLDocID'] = doc_id
        result['SQLFilename'] = matched_sql.get('Filename', '')
        
        # Get field categories
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

# Calculate statistics
print("\n5. MAPPING RESULTS:")
print("-" * 60)

total = len(df_client)
for match_type, count in sorted(match_stats.items(), key=lambda x: x[1], reverse=True):
    pct = count / total * 100
    print(f"  {match_type:25s}: {count:4d} ({pct:.1f}%)")

has_sql = len([r for r in mapping_results if r['SQLDocID']])
has_manifest = len([r for r in mapping_results if r['ManifestCode']])
total_matched = total - match_stats['no_match']

print(f"\nTotal with SQL data: {has_sql} ({has_sql/total*100:.1f}%)")
print(f"Total with Manifest code: {has_manifest} ({has_manifest/total*100:.1f}%)")
print(f"Total matched (any): {total_matched} ({total_matched/total*100:.1f}%)")

# Analyze effort
with_hours = [r for r in mapping_results if r['EstimatedHours'] > 0]
if with_hours:
    total_hours = sum(r['EstimatedHours'] for r in with_hours)
    avg_hours = total_hours / len(with_hours)
    print(f"\nEffort Analysis:")
    print(f"  Documents with field data: {len(with_hours)}")
    print(f"  Total estimated hours: {total_hours:.0f}")
    print(f"  Average hours per document: {avg_hours:.2f}")

# Check manifest-only items
manifest_only = [r for r in mapping_results if r['MatchPath'] == 'Manifest Only (no SQL)']
print(f"\n6. Manifest-Only Analysis:")
print(f"  {len(manifest_only)} templates have manifest codes but no SQL match")

if manifest_only:
    print(f"\n  Sample manifest-only items:")
    for item in manifest_only[:10]:
        print(f"    {item['ClientTitle']:15s} → Code {item['ManifestCode']}")

# Save comprehensive results
print("\n7. Saving Results...")

df_results = pd.DataFrame(mapping_results)
output_file = '../ClaudeReview/FINAL_Three_Step_Mapping.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full results
    df_results.to_excel(writer, sheet_name='Complete Mapping', index=False)
    
    # Summary
    summary = pd.DataFrame([{
        'Total Client Requirements': total,
        'With SQL Data': has_sql,
        'SQL Coverage': f"{has_sql/total*100:.1f}%",
        'With Manifest Code': has_manifest,
        'Manifest Coverage': f"{has_manifest/total*100:.1f}%",
        'Total Matched': total_matched,
        'Match Rate': f"{total_matched/total*100:.1f}%",
        'No Match': match_stats['no_match'],
        'Total Estimated Hours': sum(r['EstimatedHours'] for r in mapping_results)
    }])
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Match path breakdown
    path_df = pd.DataFrame(list(match_stats.items()), columns=['Match Path', 'Count'])
    path_df['Percentage'] = (path_df['Count'] / total * 100).round(1)
    path_df.sort_values('Count', ascending=False, inplace=True)
    path_df.to_excel(writer, sheet_name='Match Paths', index=False)
    
    # Manifest only items
    if manifest_only:
        df_manifest_only = pd.DataFrame(manifest_only)
        df_manifest_only.to_excel(writer, sheet_name='Manifest Only', index=False)
    
    # Unmatched items
    unmatched = df_results[df_results['MatchPath'] == 'No Match']
    if len(unmatched) > 0:
        unmatched.to_excel(writer, sheet_name='Unmatched', index=False)

print(f"✓ Saved to {output_file}")

# Final summary
print("\n" + "=" * 80)
print("FINAL COMPREHENSIVE MAPPING SUMMARY")
print("=" * 80)

print(f"\n✅ SUCCESS METRICS:")
print(f"  • SQL Data Coverage: {has_sql}/{total} ({has_sql/total*100:.1f}%)")
print(f"  • Manifest Mapping: {has_manifest}/{total} ({has_manifest/total*100:.1f}%)")
print(f"  • Total Matched: {total_matched}/{total} ({total_matched/total*100:.1f}%)")

if with_hours:
    print(f"\n📊 EFFORT ESTIMATES:")
    print(f"  • Documents analyzed: {len(with_hours)}")
    print(f"  • Total effort: {total_hours:.0f} hours")
    print(f"  • Average per document: {avg_hours:.2f} hours")

print(f"\n⚠️ GAPS:")
print(f"  • No match at all: {match_stats['no_match']} items")
print(f"  • Manifest but no SQL: {len(manifest_only)} items")

print("\n💡 CONCLUSION:")
if has_sql/total > 0.4:
    print("  ✓ Good SQL coverage achieved through manifest mapping")
else:
    print("  ⚠️ Limited SQL coverage - many templates not in current database")
    print("  → Need additional data sources or imports")

print("\n" + "=" * 80)
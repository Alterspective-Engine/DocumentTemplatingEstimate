import json
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re

print("=" * 80)
print("FINAL COMPREHENSIVE MAPPING - ALL DATA SOURCES")
print("=" * 80)

# Load all data sources
print("\n1. Loading All Data Sources...")

# Client Requirements
df_client = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx')
print(f"✓ Client Requirements: {len(df_client)} items")

# SQL Documents from newSQL
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)
print(f"✓ SQL Documents: {len(sql_documents)} items")

# SQL Field Analysis
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ Field Analysis: {len(field_analysis)} records")

# Main Manifest
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

# Parse manifest for mappings
manifest_mappings = {}
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    if code and name:
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip().lower()
        
        # Extract title from description (third line)
        desc_lines = description.split('\n')
        prec_title = None
        if len(desc_lines) >= 3:
            prec_title = desc_lines[2].strip().lower()
        
        manifest_mappings[clean_name] = {
            'code': code,
            'original_name': name,
            'prec_title': prec_title,
            'description': description
        }
        
        # Also store by code
        manifest_mappings[code] = {
            'code': code,
            'original_name': name,
            'prec_title': prec_title,
            'description': description
        }

print(f"✓ Manifest Mappings: {len(manifest_mappings)} entries")

# Build SQL document lookups
sql_doc_by_filename = {}
sql_doc_by_basename = {}
for doc in sql_documents:
    filename = doc.get('Filename', '')
    if filename:
        sql_doc_by_filename[filename.lower()] = doc
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_doc_by_basename[basename] = doc

print(f"✓ SQL Document Lookups built")

# Build field analysis by document
field_by_doc = defaultdict(lambda: defaultdict(int))
for record in field_analysis:
    doc_id = record['documentid']
    category = record['field_category']
    field_by_doc[doc_id][category] += 1

print("\n2. Comprehensive Matching Process...")

# Match each client requirement
match_results = []
match_stats = defaultdict(int)

for idx, row in df_client.iterrows():
    client_title = row['Current Title']
    client_title_lower = client_title.lower()
    
    result = {
        'ClientTitle': client_title,
        'ClientDescription': row['Description'],
        'ClientComplexity': row['Complexity'],
        'MatchType': 'No Match',
        'MatchedWith': None,
        'Code': None,
        'SQLDocumentID': None,
        'SQLFilename': None,
        'FieldCategories': {},
        'EstimatedHours': 0
    }
    
    matched = False
    
    # Strategy 1: Direct SQL filename match
    if client_title_lower in sql_doc_by_basename:
        doc = sql_doc_by_basename[client_title_lower]
        result['MatchType'] = 'SQL Direct Match'
        result['MatchedWith'] = doc['Filename']
        result['SQLDocumentID'] = doc['DocumentID']
        result['SQLFilename'] = doc['Filename']
        result['FieldCategories'] = dict(field_by_doc[doc['DocumentID']])
        match_stats['sql_direct'] += 1
        matched = True
    
    # Strategy 2: Check with .dot extension
    elif f"{client_title_lower}.dot" in sql_doc_by_filename:
        doc = sql_doc_by_filename[f"{client_title_lower}.dot"]
        result['MatchType'] = 'SQL with Extension'
        result['MatchedWith'] = doc['Filename']
        result['SQLDocumentID'] = doc['DocumentID']
        result['SQLFilename'] = doc['Filename']
        result['FieldCategories'] = dict(field_by_doc[doc['DocumentID']])
        match_stats['sql_extension'] += 1
        matched = True
    
    # Strategy 3: Manifest mapping then SQL
    elif client_title_lower in manifest_mappings:
        mapping = manifest_mappings[client_title_lower]
        code = mapping['code']
        # Check if code exists in SQL
        if code in sql_doc_by_basename:
            doc = sql_doc_by_basename[code]
            result['MatchType'] = 'Manifest to SQL'
            result['MatchedWith'] = f"Code {code} → {doc['Filename']}"
            result['Code'] = code
            result['SQLDocumentID'] = doc['DocumentID']
            result['SQLFilename'] = doc['Filename']
            result['FieldCategories'] = dict(field_by_doc[doc['DocumentID']])
            match_stats['manifest_to_sql'] += 1
            matched = True
        elif f"{code}.dot" in sql_doc_by_filename:
            doc = sql_doc_by_filename[f"{code}.dot"]
            result['MatchType'] = 'Manifest Code to SQL'
            result['MatchedWith'] = f"Code {code} → {doc['Filename']}"
            result['Code'] = code
            result['SQLDocumentID'] = doc['DocumentID']
            result['SQLFilename'] = doc['Filename']
            result['FieldCategories'] = dict(field_by_doc[doc['DocumentID']])
            match_stats['manifest_code_sql'] += 1
            matched = True
        else:
            result['MatchType'] = 'Manifest Only'
            result['MatchedWith'] = f"Manifest Code {code}"
            result['Code'] = code
            match_stats['manifest_only'] += 1
            matched = True
    
    # Strategy 4: Search for partial matches in SQL
    if not matched:
        for filename, doc in sql_doc_by_filename.items():
            if client_title_lower in filename or filename in client_title_lower:
                result['MatchType'] = 'SQL Partial Match'
                result['MatchedWith'] = doc['Filename']
                result['SQLDocumentID'] = doc['DocumentID']
                result['SQLFilename'] = doc['Filename']
                result['FieldCategories'] = dict(field_by_doc[doc['DocumentID']])
                match_stats['sql_partial'] += 1
                matched = True
                break
    
    # Calculate estimated hours if we have field data
    if result['FieldCategories']:
        effort_map = {
            'Reflection': 5,
            'Extended': 5,
            'Unbound': 5,
            'Search': 10,
            'If': 15,
            'If Statement': 15,
            'Built In Script': 20,
            'Scripted': 30,
            'Precedent Script': 30
        }
        
        total_minutes = 0
        for category, count in result['FieldCategories'].items():
            minutes = effort_map.get(category, 10)
            total_minutes += count * minutes
        
        # Add form creation time for unbound
        if result['FieldCategories'].get('Unbound', 0) > 0:
            total_minutes += 15
        
        result['EstimatedHours'] = round(total_minutes / 60, 2)
    
    if not matched:
        match_stats['no_match'] += 1
    
    match_results.append(result)

# Summary statistics
print("\n3. MATCHING RESULTS:")
print("-" * 40)
total = len(df_client)
for match_type, count in sorted(match_stats.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total * 100)
    print(f"  {match_type:20s}: {count:4d} ({pct:.1f}%)")

total_matched = total - match_stats['no_match']
print(f"\nTotal Matched: {total_matched} ({total_matched/total*100:.1f}%)")
print(f"Total Unmatched: {match_stats['no_match']} ({match_stats['no_match']/total*100:.1f}%)")

# Analyze matches with SQL data
sql_matches = [r for r in match_results if r['SQLDocumentID']]
print(f"\nMatches with SQL Data: {len(sql_matches)} ({len(sql_matches)/total*100:.1f}%)")

if sql_matches:
    total_hours = sum(r['EstimatedHours'] for r in sql_matches)
    avg_hours = total_hours / len(sql_matches) if sql_matches else 0
    print(f"  Total Estimated Hours: {total_hours:.0f}")
    print(f"  Average Hours per Document: {avg_hours:.2f}")

# Check ExportSandI/Precedents folders for unmatched items
print("\n4. Checking Precedents Folders for Unmatched Items...")
precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
precedent_folders = set(d.name for d in precedents_path.iterdir() if d.is_dir())

unmatched_items = [r for r in match_results if r['MatchType'] == 'No Match']
found_in_folders = []

for item in unmatched_items:
    client_title = item['ClientTitle']
    # Check if any precedent folder might contain this
    for folder in precedent_folders:
        if folder not in manifest_mappings:
            # This folder exists but isn't in the manifest
            manifest_file = precedents_path / folder / 'manifest.xml'
            if manifest_file.exists():
                try:
                    tree = ET.parse(manifest_file)
                    root = tree.getroot()
                    prec_elem = root.find('.//PRECEDENT')
                    if prec_elem:
                        prec_title = prec_elem.findtext('PrecTitle', '').lower()
                        if prec_title == client_title.lower():
                            found_in_folders.append({
                                'ClientTitle': client_title,
                                'FolderCode': folder,
                                'PrecTitle': prec_title
                            })
                            break
                except:
                    pass

if found_in_folders:
    print(f"✓ Found {len(found_in_folders)} unmatched items in Precedents folders not in manifest")
    for item in found_in_folders[:5]:
        print(f"  - {item['ClientTitle']} → Folder {item['FolderCode']}")

# Save comprehensive results
print("\n5. Saving Results...")

output_file = '../ClaudeReview/FINAL_comprehensive_mapping.xlsx'
df_results = pd.DataFrame(match_results)

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full results
    df_results.to_excel(writer, sheet_name='Complete Mapping', index=False)
    
    # Summary statistics
    stats_df = pd.DataFrame([{
        'Total Client Requirements': total,
        'Total Matched': total_matched,
        'Match Rate': f"{total_matched/total*100:.1f}%",
        'Matches with SQL Data': len(sql_matches),
        'SQL Match Rate': f"{len(sql_matches)/total*100:.1f}%",
        'Total Estimated Hours': sum(r['EstimatedHours'] for r in sql_matches),
        'No Match': match_stats['no_match']
    }])
    stats_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Match type breakdown
    match_breakdown = pd.DataFrame(list(match_stats.items()), columns=['Match Type', 'Count'])
    match_breakdown['Percentage'] = (match_breakdown['Count'] / total * 100).round(1)
    match_breakdown.sort_values('Count', ascending=False, inplace=True)
    match_breakdown.to_excel(writer, sheet_name='Match Breakdown', index=False)
    
    # Unmatched items
    df_unmatched = df_results[df_results['MatchType'] == 'No Match'][['ClientTitle', 'ClientDescription', 'ClientComplexity']]
    df_unmatched.to_excel(writer, sheet_name='Unmatched Items', index=False)
    
    # Items with effort estimates
    df_with_hours = df_results[df_results['EstimatedHours'] > 0].sort_values('EstimatedHours', ascending=False)
    df_with_hours.to_excel(writer, sheet_name='Effort Estimates', index=False)

print(f"✓ Saved to {output_file}")

# Save JSON summary
summary = {
    'total_client_requirements': total,
    'total_matched': total_matched,
    'match_rate_pct': round(total_matched/total*100, 1),
    'matches_with_sql_data': len(sql_matches),
    'sql_match_rate_pct': round(len(sql_matches)/total*100, 1),
    'total_estimated_hours': round(sum(r['EstimatedHours'] for r in sql_matches), 0),
    'match_type_breakdown': dict(match_stats),
    'unmatched_count': match_stats['no_match'],
    'found_in_unlisted_folders': len(found_in_folders)
}

with open('../ClaudeReview/FINAL_mapping_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("✓ Saved JSON summary")

# Print investigation notes
print("\n6. INVESTIGATION SUMMARY:")
print("-" * 40)
print(f"• {match_stats['no_match']} items have no match in any data source")
print(f"• {len(found_in_folders)} of these exist in Precedents folders but aren't in manifest")
print(f"• {match_stats.get('manifest_only', 0)} items found in manifest but not in SQL")
print(f"• {len(sql_matches)} items successfully matched to SQL with field analysis")

print("\n" + "=" * 80)
print("FINAL ANALYSIS COMPLETE")
print("=" * 80)
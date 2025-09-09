import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import json
import re
from collections import defaultdict
import os

print("=" * 80)
print("COMPREHENSIVE PRECEDENT MANIFEST ANALYSIS")
print("=" * 80)

# Paths
precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
scripts_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Scripts')
client_req_path = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx'

print("\n1. Loading Client Requirements...")
df_client = pd.read_excel(client_req_path)
print(f"✓ Loaded {len(df_client)} client requirements")

# Create lookup for client requirements
client_lookup = {}
for idx, row in df_client.iterrows():
    title = row['Current Title']
    # Store original and various formats
    client_lookup[title.lower()] = row
    client_lookup[title.upper()] = row
    client_lookup[title] = row
    # Remove spaces and special chars for better matching
    clean_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
    client_lookup[clean_title] = row

print(f"✓ Created lookup with {len(client_lookup)} variations")

print("\n2. Parsing Precedent Manifests...")
precedent_data = []
failed_parses = []

# Parse all manifest.xml files in Precedents folder
manifest_files = list(precedents_path.glob('*/manifest.xml'))
print(f"Found {len(manifest_files)} manifest files to parse")

for manifest_file in manifest_files:
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        
        # Find PRECEDENT element
        prec_elem = root.find('.//PRECEDENT')
        if prec_elem is not None:
            # Extract key fields
            prec_data = {
                'ManifestPath': str(manifest_file),
                'FolderName': manifest_file.parent.name,
                'PrecID': prec_elem.findtext('PrecID', ''),
                'PrecTitle': prec_elem.findtext('PrecTitle', ''),
                'PrecType': prec_elem.findtext('PrecType', ''),
                'PrecCategory': prec_elem.findtext('PrecCategory', ''),
                'PrecSubCategory': prec_elem.findtext('PrecSubCategory', ''),
                'PrecDesc': prec_elem.findtext('PrecDesc', ''),
                'PrecPath': prec_elem.findtext('PrecPath', ''),
                'PrecLibrary': prec_elem.findtext('PrecLibrary', ''),
                'PrecLanguage': prec_elem.findtext('PrecLanguage', ''),
                'PrecPubName': prec_elem.findtext('PrecPubName', ''),
                'PrecPreview': prec_elem.findtext('PrecPreview', ''),
                'PrecScript': prec_elem.findtext('PrecScript', ''),
                'PrecExtension': prec_elem.findtext('precExtension', ''),
                'PrecMS': prec_elem.findtext('PrecMS', ''),
                'PrecMultiPrec': prec_elem.findtext('PrecMultiPrec', ''),
                'Created': prec_elem.findtext('Created', ''),
                'Updated': prec_elem.findtext('Updated', ''),
                'udFormNo': prec_elem.findtext('udFormNo', ''),
                'PrecMinorCategory': prec_elem.findtext('PrecMinorCategory', ''),
            }
            
            # Analyze PrecPreview for field complexity
            preview = prec_data['PrecPreview']
            if preview:
                # Count different field types in preview
                prec_data['IF_Count'] = preview.count('IF &#x13;') + preview.count('IF&#x13;')
                prec_data['DOCVARIABLE_Count'] = preview.count('DOCVARIABLE')
                prec_data['MERGEFORMAT_Count'] = preview.count('MERGEFORMAT')
                prec_data['SELECT_Count'] = preview.count('Select ')
                prec_data['ASSOC_Count'] = preview.count('ASSOC')
                prec_data['UDSCH_Count'] = preview.count('UDSCH')
                prec_data['Preview_Length'] = len(preview)
            else:
                prec_data['IF_Count'] = 0
                prec_data['DOCVARIABLE_Count'] = 0
                prec_data['MERGEFORMAT_Count'] = 0
                prec_data['SELECT_Count'] = 0
                prec_data['ASSOC_Count'] = 0
                prec_data['UDSCH_Count'] = 0
                prec_data['Preview_Length'] = 0
            
            precedent_data.append(prec_data)
    except Exception as e:
        failed_parses.append({
            'File': str(manifest_file),
            'Error': str(e)
        })

print(f"✓ Successfully parsed {len(precedent_data)} precedent manifests")
if failed_parses:
    print(f"⚠ Failed to parse {len(failed_parses)} files")

# Convert to DataFrame
df_precedents = pd.DataFrame(precedent_data)

print("\n3. Matching Precedents to Client Requirements...")

# Try multiple matching strategies
match_results = []
unmatched_client_reqs = []
unmatched_precedents = []

# Create various lookups for precedents
prec_by_title = {p['PrecTitle'].lower(): p for p in precedent_data if p['PrecTitle']}
prec_by_id = {p['PrecID']: p for p in precedent_data if p['PrecID']}
prec_by_folder = {p['FolderName']: p for p in precedent_data}

# Track matching statistics
match_stats = {
    'exact_title': 0,
    'lowercase_title': 0,
    'clean_title': 0,
    'folder_name': 0,
    'partial_match': 0,
    'no_match': 0
}

for idx, client_row in df_client.iterrows():
    client_title = client_row['Current Title']
    matched = False
    match_info = {
        'ClientTitle': client_title,
        'ClientDescription': client_row['Description'],
        'ClientComplexity': client_row['Complexity']
    }
    
    # Strategy 1: Exact title match
    if client_title.lower() in prec_by_title:
        prec = prec_by_title[client_title.lower()]
        match_info.update(prec)
        match_info['MatchType'] = 'Exact Title'
        match_stats['exact_title'] += 1
        matched = True
    
    # Strategy 2: Clean title match (remove special chars)
    elif not matched:
        clean_client = re.sub(r'[^a-zA-Z0-9]', '', client_title.lower())
        for prec_title, prec in prec_by_title.items():
            clean_prec = re.sub(r'[^a-zA-Z0-9]', '', prec_title)
            if clean_client == clean_prec:
                match_info.update(prec)
                match_info['MatchType'] = 'Clean Title'
                match_stats['clean_title'] += 1
                matched = True
                break
    
    # Strategy 3: Check if client title matches folder name
    if not matched and client_title in prec_by_folder:
        prec = prec_by_folder[client_title]
        match_info.update(prec)
        match_info['MatchType'] = 'Folder Name'
        match_stats['folder_name'] += 1
        matched = True
    
    # Strategy 4: Partial match (if title contains or is contained in precedent title)
    if not matched:
        for prec_title, prec in prec_by_title.items():
            if client_title.lower() in prec_title or prec_title in client_title.lower():
                match_info.update(prec)
                match_info['MatchType'] = 'Partial Match'
                match_stats['partial_match'] += 1
                matched = True
                break
    
    if matched:
        match_results.append(match_info)
    else:
        match_info['MatchType'] = 'No Match'
        match_stats['no_match'] += 1
        match_results.append(match_info)
        unmatched_client_reqs.append(client_title)

# Find precedents not matched to any client requirement
matched_prec_ids = set([m.get('PrecID') for m in match_results if m.get('PrecID')])
for prec in precedent_data:
    if prec['PrecID'] not in matched_prec_ids:
        unmatched_precedents.append(prec)

print("\n4. MATCHING STATISTICS:")
print("-" * 40)
total_client_reqs = len(df_client)
for match_type, count in match_stats.items():
    pct = (count / total_client_reqs * 100) if total_client_reqs > 0 else 0
    print(f"  {match_type:15s}: {count:4d} ({pct:.1f}%)")

print(f"\nTotal Matched: {total_client_reqs - match_stats['no_match']} ({(total_client_reqs - match_stats['no_match'])/total_client_reqs*100:.1f}%)")

# Analyze field complexity from PrecPreview
print("\n5. Analyzing Field Complexity from PrecPreview...")

complexity_analysis = []
for match in match_results:
    if match.get('PrecPreview'):
        # Estimate effort based on field counts
        if_count = match.get('IF_Count', 0)
        docvar_count = match.get('DOCVARIABLE_Count', 0)
        select_count = match.get('SELECT_Count', 0)
        assoc_count = match.get('ASSOC_Count', 0)
        
        # Calculate estimated minutes
        estimated_minutes = (
            if_count * 15 +  # IF statements: 15 min each
            docvar_count * 10 +  # DOCVARIABLE: 10 min each
            select_count * 10 +  # SELECT: 10 min each
            assoc_count * 5  # ASSOC: 5 min each
        )
        
        complexity_analysis.append({
            'ClientTitle': match['ClientTitle'],
            'PrecTitle': match.get('PrecTitle', ''),
            'IF_Count': if_count,
            'DOCVARIABLE_Count': docvar_count,
            'SELECT_Count': select_count,
            'ASSOC_Count': assoc_count,
            'Preview_Length': match.get('Preview_Length', 0),
            'EstimatedMinutes': estimated_minutes,
            'EstimatedHours': round(estimated_minutes / 60, 2)
        })

df_complexity = pd.DataFrame(complexity_analysis)

if len(df_complexity) > 0:
    print(f"✓ Analyzed {len(df_complexity)} precedents with preview data")
    print(f"  Average estimated hours: {df_complexity['EstimatedHours'].mean():.2f}")
    print(f"  Total estimated hours: {df_complexity['EstimatedHours'].sum():.0f}")

# Parse Script manifests for additional data
print("\n6. Parsing Script Manifests...")
script_data = []
script_manifest_files = list(scripts_path.glob('*/manifest.xml'))
print(f"Found {len(script_manifest_files)} script manifest files")

for manifest_file in script_manifest_files[:50]:  # Sample first 50
    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        
        # Different structure for scripts
        script_elem = root.find('.//SCRIPT')
        if script_elem is not None:
            script_info = {
                'ScriptID': script_elem.findtext('scrID', ''),
                'ScriptCode': script_elem.findtext('scrCode', ''),
                'ScriptName': script_elem.findtext('scrName', ''),
                'ScriptType': script_elem.findtext('scrType', ''),
                'ScriptVersion': script_elem.findtext('scrVersion', ''),
                'FolderName': manifest_file.parent.name
            }
            script_data.append(script_info)
    except:
        pass

print(f"✓ Parsed {len(script_data)} script manifests")

# Save comprehensive results
print("\n7. Saving Results...")

output_file = '../ClaudeReview/precedent_manifest_analysis.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # All matches
    df_matches = pd.DataFrame(match_results)
    df_matches.to_excel(writer, sheet_name='Client to Precedent Mapping', index=False)
    
    # Match statistics
    stats_df = pd.DataFrame([match_stats])
    stats_df.to_excel(writer, sheet_name='Match Statistics', index=False)
    
    # Complexity analysis
    if len(df_complexity) > 0:
        df_complexity.to_excel(writer, sheet_name='Complexity Analysis', index=False)
    
    # All precedents
    df_precedents.to_excel(writer, sheet_name='All Precedents', index=False)
    
    # Unmatched client requirements
    if unmatched_client_reqs:
        pd.DataFrame({'UnmatchedClientTitle': unmatched_client_reqs}).to_excel(
            writer, sheet_name='Unmatched Client Reqs', index=False)
    
    # Unmatched precedents
    if unmatched_precedents:
        pd.DataFrame(unmatched_precedents).to_excel(
            writer, sheet_name='Unmatched Precedents', index=False)
    
    # Scripts
    if script_data:
        pd.DataFrame(script_data).to_excel(writer, sheet_name='Scripts', index=False)

print(f"✓ Saved to {output_file}")

# Save JSON summary
summary = {
    'total_client_requirements': len(df_client),
    'total_precedents_parsed': len(precedent_data),
    'match_statistics': match_stats,
    'total_matched': total_client_reqs - match_stats['no_match'],
    'match_rate': f"{(total_client_reqs - match_stats['no_match'])/total_client_reqs*100:.1f}%",
    'precedents_with_preview': len([p for p in precedent_data if p.get('PrecPreview')]),
    'scripts_parsed': len(script_data),
    'field_type_summary': {
        'IF_statements': sum([p.get('IF_Count', 0) for p in precedent_data]),
        'DOCVARIABLE': sum([p.get('DOCVARIABLE_Count', 0) for p in precedent_data]),
        'SELECT': sum([p.get('SELECT_Count', 0) for p in precedent_data]),
        'ASSOC': sum([p.get('ASSOC_Count', 0) for p in precedent_data])
    }
}

with open('../ClaudeReview/precedent_manifest_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("✓ Saved JSON summary")

# Print unmatched examples for investigation
print("\n8. SAMPLES FOR INVESTIGATION:")
print("-" * 40)

if unmatched_client_reqs:
    print(f"\nUnmatched Client Requirements (first 10):")
    for title in unmatched_client_reqs[:10]:
        print(f"  - {title}")

print(f"\nSample Precedent Titles (first 10):")
for prec in precedent_data[:10]:
    print(f"  - PrecTitle: {prec['PrecTitle']:20s} | Folder: {prec['FolderName']:10s} | Category: {prec.get('PrecCategory', 'N/A')}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
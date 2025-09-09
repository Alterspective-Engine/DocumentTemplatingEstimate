import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import json
import re
from collections import defaultdict
import os

print("=" * 80)
print("COMPREHENSIVE MANIFEST MAPPING ANALYSIS")
print("=" * 80)

# Paths
main_manifest_path = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml'
precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
client_req_path = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx'

print("\n1. Loading Client Requirements...")
df_client = pd.read_excel(client_req_path)
print(f"✓ Loaded {len(df_client)} client requirements")

# Create comprehensive client lookup
client_lookup = {}
client_list = []
for idx, row in df_client.iterrows():
    title = row['Current Title']
    client_list.append({
        'ClientTitle': title,
        'ClientDescription': row['Description'],
        'ClientComplexity': row['Complexity']
    })
    # Store in various formats for matching
    client_lookup[title.lower()] = idx
    client_lookup[title.upper()] = idx
    client_lookup[title] = idx

print(f"✓ Created lookup for {len(client_list)} client requirements")

print("\n2. Parsing Main Manifest (ExportSandI.Manifest.xml)...")

# Parse main manifest to get code-to-name mappings
tree = ET.parse(main_manifest_path)
root = tree.getroot()

code_to_name = {}
name_to_code = {}
code_to_info = {}

# Parse Items elements
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    if code and name:
        # Clean the name (remove version indicators like "(del:1)")
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip()
        clean_name_lower = clean_name.lower()
        
        # Store mapping
        code_to_name[code] = clean_name
        name_to_code[clean_name_lower] = code
        
        # Parse description to extract title (third line typically contains the title)
        desc_lines = description.split('\n')
        prec_title = None
        if len(desc_lines) >= 3:
            # Third line often contains the actual title
            prec_title = desc_lines[2].strip()
        
        code_to_info[code] = {
            'Name': name,
            'CleanName': clean_name,
            'PrecTitle': prec_title,
            'Description': description,
            'Category': None,
            'Type': None
        }
        
        # Extract category and type from description
        for line in desc_lines:
            if 'Category :' in line:
                code_to_info[code]['Category'] = line.split(':', 1)[1].strip()
            elif 'Type :' in line:
                code_to_info[code]['Type'] = line.split(':', 1)[1].strip()

print(f"✓ Found {len(code_to_name)} precedent codes in main manifest")

print("\n3. Reading Precedent Folder Manifests...")

# Now read the individual manifest.xml files from precedent folders
precedent_details = {}
parse_failures = []

for code, info in code_to_info.items():
    manifest_file = precedents_path / code / 'manifest.xml'
    
    if manifest_file.exists():
        try:
            tree = ET.parse(manifest_file)
            root = tree.getroot()
            
            prec_elem = root.find('.//PRECEDENT')
            if prec_elem is not None:
                # Extract detailed information
                details = {
                    'Code': code,
                    'MainManifestName': info['Name'],
                    'MainManifestCleanName': info['CleanName'],
                    'MainManifestPrecTitle': info['PrecTitle'],
                    'PrecID': prec_elem.findtext('PrecID', ''),
                    'PrecTitle': prec_elem.findtext('PrecTitle', ''),
                    'PrecType': prec_elem.findtext('PrecType', ''),
                    'PrecCategory': prec_elem.findtext('PrecCategory', ''),
                    'PrecSubCategory': prec_elem.findtext('PrecSubCategory', ''),
                    'PrecDesc': prec_elem.findtext('PrecDesc', ''),
                    'PrecPath': prec_elem.findtext('PrecPath', ''),
                    'PrecLibrary': prec_elem.findtext('PrecLibrary', ''),
                    'PrecPreview': prec_elem.findtext('PrecPreview', ''),
                    'PrecScript': prec_elem.findtext('PrecScript', ''),
                    'Created': prec_elem.findtext('Created', ''),
                    'Updated': prec_elem.findtext('Updated', ''),
                }
                
                # Analyze PrecPreview for field complexity
                preview = details.get('PrecPreview', '')
                if preview:
                    details['IF_Count'] = preview.count('IF &#x13;') + preview.count('IF&#x13;')
                    details['DOCVARIABLE_Count'] = preview.count('DOCVARIABLE')
                    details['MERGEFORMAT_Count'] = preview.count('MERGEFORMAT')
                    details['SELECT_Count'] = preview.count('Select ')
                    details['ASSOC_Count'] = preview.count('ASSOC')
                    details['UDSCH_Count'] = preview.count('UDSCH')
                    details['Preview_Length'] = len(preview)
                else:
                    details['IF_Count'] = 0
                    details['DOCVARIABLE_Count'] = 0
                    details['MERGEFORMAT_Count'] = 0
                    details['SELECT_Count'] = 0
                    details['ASSOC_Count'] = 0
                    details['UDSCH_Count'] = 0
                    details['Preview_Length'] = 0
                
                precedent_details[code] = details
        except Exception as e:
            parse_failures.append({'Code': code, 'Error': str(e)})

print(f"✓ Successfully parsed {len(precedent_details)} precedent folder manifests")
if parse_failures:
    print(f"⚠ Failed to parse {len(parse_failures)} manifests")

print("\n4. Advanced Matching: Client Requirements to Precedents...")

# Create multiple matching strategies
match_results = []
match_stats = defaultdict(int)

for client_item in client_list:
    client_title = client_item['ClientTitle']
    client_title_lower = client_title.lower()
    
    matched = False
    match_info = client_item.copy()
    
    # Strategy 1: Direct match with MainManifestCleanName
    if client_title_lower in name_to_code:
        code = name_to_code[client_title_lower]
        if code in precedent_details:
            match_info.update(precedent_details[code])
            match_info['MatchType'] = 'Direct Name Match'
            match_info['MatchedCode'] = code
            match_stats['direct_name'] += 1
            matched = True
    
    # Strategy 2: Match with PrecTitle from precedent manifests
    if not matched:
        for code, details in precedent_details.items():
            prec_title = details.get('PrecTitle', '').lower()
            if prec_title and (prec_title == client_title_lower):
                match_info.update(details)
                match_info['MatchType'] = 'PrecTitle Match'
                match_info['MatchedCode'] = code
                match_stats['prec_title'] += 1
                matched = True
                break
    
    # Strategy 3: Match with MainManifestPrecTitle
    if not matched:
        for code, info in code_to_info.items():
            main_prec_title = info.get('PrecTitle', '').lower()
            if main_prec_title and (main_prec_title == client_title_lower):
                if code in precedent_details:
                    match_info.update(precedent_details[code])
                else:
                    match_info.update({
                        'Code': code,
                        'MainManifestName': info['Name'],
                        'MainManifestCleanName': info['CleanName'],
                        'MainManifestPrecTitle': info['PrecTitle']
                    })
                match_info['MatchType'] = 'Main Manifest Title Match'
                match_info['MatchedCode'] = code
                match_stats['main_manifest_title'] += 1
                matched = True
                break
    
    # Strategy 4: Partial match
    if not matched:
        for code, details in precedent_details.items():
            prec_title = details.get('PrecTitle', '').lower()
            main_name = details.get('MainManifestCleanName', '').lower()
            
            # Check if client title is contained in or contains precedent titles
            if prec_title and (client_title_lower in prec_title or prec_title in client_title_lower):
                match_info.update(details)
                match_info['MatchType'] = 'Partial Match'
                match_info['MatchedCode'] = code
                match_stats['partial'] += 1
                matched = True
                break
            elif main_name and (client_title_lower in main_name or main_name in client_title_lower):
                match_info.update(details)
                match_info['MatchType'] = 'Partial Name Match'
                match_info['MatchedCode'] = code
                match_stats['partial'] += 1
                matched = True
                break
    
    # Strategy 5: Check if client title matches a code directly
    if not matched and client_title in code_to_info:
        code = client_title
        if code in precedent_details:
            match_info.update(precedent_details[code])
        else:
            match_info.update({
                'Code': code,
                'MainManifestName': code_to_info[code]['Name']
            })
        match_info['MatchType'] = 'Code Match'
        match_info['MatchedCode'] = code
        match_stats['code_match'] += 1
        matched = True
    
    if not matched:
        match_info['MatchType'] = 'No Match'
        match_info['MatchedCode'] = None
        match_stats['no_match'] += 1
    
    match_results.append(match_info)

print("\n5. MATCHING RESULTS:")
print("-" * 40)
total = len(client_list)
for match_type, count in match_stats.items():
    pct = (count / total * 100) if total > 0 else 0
    print(f"  {match_type:25s}: {count:4d} ({pct:.1f}%)")

total_matched = total - match_stats['no_match']
print(f"\nTotal Matched: {total_matched} ({total_matched/total*100:.1f}%)")
print(f"Total Unmatched: {match_stats['no_match']} ({match_stats['no_match']/total*100:.1f}%)")

# Analyze complexity for matched items
print("\n6. Analyzing Field Complexity...")
complexity_data = []
for match in match_results:
    if match.get('MatchedCode') and match.get('Preview_Length', 0) > 0:
        # Calculate estimated effort
        if_count = match.get('IF_Count', 0)
        docvar_count = match.get('DOCVARIABLE_Count', 0)
        select_count = match.get('SELECT_Count', 0)
        assoc_count = match.get('ASSOC_Count', 0)
        
        estimated_minutes = (
            if_count * 15 +
            docvar_count * 10 +
            select_count * 10 +
            assoc_count * 5
        )
        
        complexity_data.append({
            'ClientTitle': match['ClientTitle'],
            'Code': match.get('MatchedCode'),
            'PrecTitle': match.get('PrecTitle', ''),
            'PrecPath': match.get('PrecPath', ''),
            'IF_Count': if_count,
            'DOCVARIABLE_Count': docvar_count,
            'SELECT_Count': select_count,
            'ASSOC_Count': assoc_count,
            'EstimatedMinutes': estimated_minutes,
            'EstimatedHours': round(estimated_minutes / 60, 2),
            'Category': match.get('PrecCategory', ''),
            'Type': match.get('PrecType', '')
        })

if complexity_data:
    df_complexity = pd.DataFrame(complexity_data)
    print(f"✓ Analyzed {len(complexity_data)} templates with field data")
    print(f"  Total estimated hours: {df_complexity['EstimatedHours'].sum():.0f}")
    print(f"  Average hours per template: {df_complexity['EstimatedHours'].mean():.2f}")

# Save comprehensive results
print("\n7. Saving Results...")

output_file = '../ClaudeReview/comprehensive_manifest_mapping.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full mapping results
    df_matches = pd.DataFrame(match_results)
    df_matches.to_excel(writer, sheet_name='Complete Mapping', index=False)
    
    # Match statistics
    stats_df = pd.DataFrame(list(match_stats.items()), columns=['Match Type', 'Count'])
    stats_df['Percentage'] = (stats_df['Count'] / total * 100).round(1)
    stats_df.to_excel(writer, sheet_name='Match Statistics', index=False)
    
    # Complexity analysis
    if complexity_data:
        df_complexity.to_excel(writer, sheet_name='Complexity Analysis', index=False)
    
    # Unmatched client requirements
    unmatched = [m for m in match_results if m['MatchType'] == 'No Match']
    if unmatched:
        df_unmatched = pd.DataFrame(unmatched)[['ClientTitle', 'ClientDescription', 'ClientComplexity']]
        df_unmatched.to_excel(writer, sheet_name='Unmatched Client Reqs', index=False)
    
    # All precedent details
    if precedent_details:
        df_prec = pd.DataFrame(list(precedent_details.values()))
        df_prec.to_excel(writer, sheet_name='All Precedent Details', index=False)

print(f"✓ Saved to {output_file}")

# Save JSON summary
summary = {
    'analysis_date': pd.Timestamp.now().isoformat(),
    'total_client_requirements': len(client_list),
    'total_codes_in_main_manifest': len(code_to_name),
    'total_precedent_folders_parsed': len(precedent_details),
    'matching_statistics': dict(match_stats),
    'total_matched': total_matched,
    'match_rate': f"{total_matched/total*100:.1f}%",
    'templates_with_field_data': len(complexity_data) if complexity_data else 0,
    'total_estimated_hours': df_complexity['EstimatedHours'].sum() if complexity_data else 0
}

with open('../ClaudeReview/comprehensive_manifest_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("✓ Saved JSON summary")

# Print examples of unmatched for investigation
print("\n8. INVESTIGATION SAMPLES:")
print("-" * 40)

if unmatched:
    print(f"\nUnmatched Client Requirements (first 20):")
    for item in unmatched[:20]:
        print(f"  - {item['ClientTitle']}")
    
    print(f"\n  Total unmatched: {len(unmatched)}")

# Show some successful matches
matched_samples = [m for m in match_results if m['MatchType'] != 'No Match'][:10]
if matched_samples:
    print(f"\nSuccessful Match Examples:")
    for match in matched_samples:
        print(f"  Client: {match['ClientTitle']:15s} → Code: {match.get('MatchedCode', 'N/A'):10s} [{match['MatchType']}]")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
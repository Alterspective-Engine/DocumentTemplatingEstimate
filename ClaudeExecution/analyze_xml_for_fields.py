import xml.etree.ElementTree as ET
import pandas as pd
import base64
import re
from pathlib import Path
from collections import defaultdict
import json

print("=" * 80)
print("ANALYZING XML FILES FOR FIELD INFORMATION")
print("=" * 80)

# Load the missing documents list
df_mapping = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ClaudeReview/ULTIMATE_Mapping_Solution.xlsx')
missing_docs = df_mapping[df_mapping['SQLDocID'].isna() & df_mapping['ManifestCode'].notna()].copy()
print(f"\n1. Found {len(missing_docs)} documents missing SQL data")

# Load manifest to get precedent mappings
manifest_path = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/ExportSandI.Manifest.xml'
print(f"\n2. Loading manifest from {manifest_path}")

tree = ET.parse(manifest_path)
root = tree.getroot()

# Build code to precedent ID mapping
code_to_precid = {}
for item in root.findall('.//Item'):
    code = item.find('Code')
    if code is not None and code.text:
        # Look for PrecID in the item
        for elem in item:
            if elem.tag == 'PrecID' and elem.text:
                code_to_precid[code.text] = elem.text
                break

print(f"✓ Found {len(code_to_precid)} code to PrecID mappings")

# Now check Scripts folder for field references
print("\n3. Analyzing Scripts folder for field patterns...")

scripts_dir = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Scripts')
field_patterns_by_code = defaultdict(lambda: defaultdict(int))

# Pattern matching for different field types
patterns = {
    'If_Statement': [
        r'if\s*\([^)]+\)',
        r'IF\s*\([^)]+\)',
        r'\.Visible\s*=.*[Tt]rue|[Ff]alse',
        r'\.Enabled\s*=.*[Tt]rue|[Ff]alse'
    ],
    'Scripted': [
        r'public\s+class\s+_\d+',
        r'protected\s+override\s+void',
        r'\.ApplyParams\(\)',
        r'\.Params\.Add\('
    ],
    'Search': [
        r'GetWizard\(',
        r'\.Search\(',
        r'SearchQuery\(',
        r'DataTable.*=.*Select'
    ],
    'Reflection': [
        r'\.GetField\(',
        r'\.GetProperty\(',
        r'System\.Reflection',
        r'\.FieldValue'
    ],
    'Built_In_Script': [
        r'FWBS\.OMS\.Script',
        r'ScriptType',
        r'\.CurrentSession\.',
        r'Session\.CurrentFile'
    ]
}

# Track scripts analyzed
scripts_analyzed = 0
scripts_with_data = 0

for script_folder in scripts_dir.iterdir():
    if script_folder.is_dir():
        manifest_file = script_folder / 'manifest.xml'
        if manifest_file.exists():
            scripts_analyzed += 1
            script_code = script_folder.name.replace('_', '')
            
            try:
                # Parse the script XML
                script_tree = ET.parse(manifest_file)
                script_root = script_tree.getroot()
                
                # Find the scrText element which contains the encoded script
                scr_text = script_root.find('.//scrText')
                if scr_text is not None and scr_text.text:
                    # The text is HTML encoded and then contains base64
                    text = scr_text.text
                    # Extract base64 content between <units> tags
                    units_match = re.search(r'&lt;units[^&]*&gt;([^&]+)&lt;/units&gt;', text)
                    if units_match:
                        try:
                            # Decode base64
                            decoded = base64.b64decode(units_match.group(1)).decode('utf-8', errors='ignore')
                            
                            # Count field patterns
                            for field_type, pattern_list in patterns.items():
                                for pattern in pattern_list:
                                    matches = len(re.findall(pattern, decoded))
                                    if matches > 0:
                                        field_patterns_by_code[script_code][field_type] += matches
                            
                            if field_patterns_by_code[script_code]:
                                scripts_with_data += 1
                        except:
                            pass
            except:
                pass

print(f"✓ Analyzed {scripts_analyzed} scripts, found patterns in {scripts_with_data}")

# Now check Precedents folder
print("\n4. Analyzing Precedents folder...")

prec_dir = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
prec_patterns_by_id = defaultdict(lambda: defaultdict(int))

prec_analyzed = 0
prec_with_data = 0

for prec_folder in prec_dir.iterdir():
    if prec_folder.is_dir():
        manifest_file = prec_folder / 'manifest.xml'
        if manifest_file.exists():
            prec_analyzed += 1
            prec_id = prec_folder.name
            
            try:
                # Parse the precedent XML
                prec_tree = ET.parse(manifest_file)
                prec_root = prec_tree.getroot()
                
                # Check for script reference
                prec_script = prec_root.find('.//PrecScript')
                if prec_script is not None and prec_script.text:
                    # This precedent uses a script
                    script_code = prec_script.text.replace('_', '')
                    if script_code in field_patterns_by_code:
                        prec_patterns_by_id[prec_id] = field_patterns_by_code[script_code].copy()
                        prec_with_data += 1
                
                # Also check precXML for patterns
                prec_xml = prec_root.find('.//precXML')
                if prec_xml is not None and prec_xml.text:
                    # Decode HTML entities
                    decoded_xml = prec_xml.text.replace('&lt;', '<').replace('&gt;', '>')
                    for field_type, pattern_list in patterns.items():
                        for pattern in pattern_list:
                            matches = len(re.findall(pattern, decoded_xml))
                            if matches > 0:
                                prec_patterns_by_id[prec_id][field_type] += matches
                                
            except:
                pass

print(f"✓ Analyzed {prec_analyzed} precedents, found patterns in {prec_with_data}")

# Now estimate complexity for missing documents
print("\n5. Estimating complexity for missing documents based on XML analysis...")

missing_estimates = []
for idx, row in missing_docs.iterrows():
    code = str(row['ManifestCode'])
    title = row['ClientTitle']
    
    # Initialize field counts
    field_counts = defaultdict(int)
    
    # Check if we have script data for this code
    if code in field_patterns_by_code:
        field_counts = field_patterns_by_code[code].copy()
    
    # Check if we have precedent data via PrecID
    if code in code_to_precid:
        prec_id = code_to_precid[code]
        if prec_id in prec_patterns_by_id:
            for field_type, count in prec_patterns_by_id[prec_id].items():
                field_counts[field_type] += count
    
    # Calculate totals
    total_fields = sum(field_counts.values())
    if_statements = field_counts.get('If_Statement', 0)
    scripted_fields = field_counts.get('Scripted', 0) + field_counts.get('Built_In_Script', 0)
    
    # Apply complexity rules
    if total_fields < 10 and scripted_fields == 0 and if_statements <= 2:
        complexity = 'Simple'
        estimated_hours = 1.08  # Average from analyzed Simple docs
    elif 10 <= total_fields <= 20 and scripted_fields < 5 and if_statements <= 20:
        complexity = 'Moderate'
        estimated_hours = 8.91  # Average from analyzed Moderate docs
    else:
        complexity = 'Complex'
        estimated_hours = 67.77  # Average from analyzed Complex docs
    
    # If no fields found in XML, use conservative estimate
    if total_fields == 0:
        complexity = 'Unknown'
        estimated_hours = 29.82  # Overall average
    
    missing_estimates.append({
        'ClientTitle': title,
        'ManifestCode': code,
        'XML_Total_Fields': total_fields,
        'XML_IF_Statements': if_statements,
        'XML_Scripted_Fields': scripted_fields,
        'XML_Complexity': complexity,
        'XML_Estimated_Hours': estimated_hours,
        'Data_Source': 'XML Analysis' if total_fields > 0 else 'No XML Data'
    })

df_xml_estimates = pd.DataFrame(missing_estimates)

# Summary statistics
print("\n6. Summary of XML-based analysis:")
print(f"  Documents with XML field data: {len(df_xml_estimates[df_xml_estimates['XML_Total_Fields'] > 0])}")
print(f"  Documents without XML data: {len(df_xml_estimates[df_xml_estimates['XML_Total_Fields'] == 0])}")

# Complexity distribution
complexity_dist = df_xml_estimates['XML_Complexity'].value_counts()
print("\nComplexity distribution from XML:")
for complexity, count in complexity_dist.items():
    pct = count / len(df_xml_estimates) * 100
    print(f"  {complexity:10s}: {count:3d} ({pct:5.1f}%)")

# Save results
output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/XML_Based_Estimates.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_xml_estimates.to_excel(writer, sheet_name='XML_Estimates', index=False)
    
    # Summary sheet
    summary = pd.DataFrame([{
        'Total_Missing_Documents': len(missing_docs),
        'Documents_With_XML_Data': len(df_xml_estimates[df_xml_estimates['XML_Total_Fields'] > 0]),
        'Documents_Without_Data': len(df_xml_estimates[df_xml_estimates['XML_Total_Fields'] == 0]),
        'Total_Estimated_Hours': df_xml_estimates['XML_Estimated_Hours'].sum(),
        'Average_Hours_Per_Doc': df_xml_estimates['XML_Estimated_Hours'].mean()
    }]).T
    summary.to_excel(writer, sheet_name='Summary')

print(f"\n✓ Saved XML-based estimates to {output_file}")

# Compare with previous estimates
print("\n7. Comparison with pattern-based estimates:")
print(f"  XML-based total: {df_xml_estimates['XML_Estimated_Hours'].sum():.0f} hours")
print(f"  Previous estimate: 6,204 hours")
print(f"  Difference: {df_xml_estimates['XML_Estimated_Hours'].sum() - 6204:.0f} hours")

print("\n" + "=" * 80)
print("XML ANALYSIS COMPLETE")
print("=" * 80)
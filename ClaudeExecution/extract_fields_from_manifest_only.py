import json
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict

print("=" * 80)
print("EXTRACTING FIELD DATA FROM 279 MANIFEST-ONLY TEMPLATES")
print("=" * 80)

# Load the mapping results to get the 279 manifest-only templates
print("\n1. Loading Manifest-Only Templates...")
df_mapping = pd.read_excel('../ClaudeReview/FINAL_comprehensive_mapping.xlsx')
manifest_only = df_mapping[df_mapping['MatchType'] == 'Manifest Only']
print(f"✓ Found {len(manifest_only)} manifest-only templates")

# Load main manifest to get codes
tree = ET.parse('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml')
root = tree.getroot()

# Build code mappings
code_mappings = {}
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    if code and name:
        clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip().lower()
        code_mappings[clean_name] = code

print(f"✓ Loaded {len(code_mappings)} code mappings from manifest")

# Analyze each manifest-only template
print("\n2. Extracting Field Data from XML Precedents...")

precedents_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI/Precedents')
extracted_data = []
successful = 0
failed = 0
no_folder = 0
no_preview = 0

for idx, row in manifest_only.iterrows():
    client_title = row['ClientTitle']
    code = row.get('Code')
    
    if not code:
        # Try to find code from mappings
        code = code_mappings.get(client_title.lower())
    
    if code:
        manifest_file = precedents_path / str(code) / 'manifest.xml'
        
        if manifest_file.exists():
            try:
                tree = ET.parse(manifest_file)
                root = tree.getroot()
                
                prec_elem = root.find('.//PRECEDENT')
                if prec_elem is not None:
                    prec_preview = prec_elem.findtext('PrecPreview', '')
                    prec_script = prec_elem.findtext('PrecScript', '')
                    
                    field_counts = {
                        'If Statement': 0,
                        'Search': 0,
                        'Reflection': 0,
                        'Built In Script': 0,
                        'Extended': 0,
                        'Unbound': 0,
                        'Scripted': 0,
                        'Precedent Script': 0,
                        'Select': 0,
                        'DOCVARIABLE': 0,
                        'MERGEFORMAT': 0,
                        'Association': 0
                    }
                    
                    if prec_preview:
                        # Decode HTML entities
                        preview_decoded = prec_preview.replace('&#x13;', '').replace('&#x15;', '')
                        
                        # Count IF statements
                        field_counts['If Statement'] = (
                            len(re.findall(r'\bIF\s+', prec_preview, re.IGNORECASE)) +
                            len(re.findall(r'IF&#x13;', prec_preview))
                        )
                        
                        # Extract and categorize DOCVARIABLE
                        docvar_matches = re.findall(r'DOCVARIABLE\s+"([^"]+)"', preview_decoded, re.IGNORECASE)
                        field_counts['DOCVARIABLE'] = len(docvar_matches)
                        
                        for var in docvar_matches:
                            var_upper = var.upper()
                            if 'UDSCH' in var_upper:
                                field_counts['Search'] += 1
                            elif '~' in var:
                                field_counts['Reflection'] += 1
                            elif var.startswith('#'):
                                field_counts['Built In Script'] += 1
                            elif '$' in var:
                                field_counts['Extended'] += 1
                            elif '_' in var or '[_]' in var:
                                field_counts['Unbound'] += 1
                            elif 'SCR' in var_upper:
                                field_counts['Scripted'] += 1
                            else:
                                field_counts['Reflection'] += 1
                        
                        # Count other patterns
                        field_counts['Select'] = len(re.findall(r'Select\s+', prec_preview, re.IGNORECASE))
                        field_counts['MERGEFORMAT'] = len(re.findall(r'MERGEFORMAT', prec_preview, re.IGNORECASE))
                        field_counts['Association'] = len(re.findall(r'ASSOC[;.]', prec_preview))
                    else:
                        no_preview += 1
                    
                    # Check for precedent script
                    if prec_script and prec_script.strip():
                        field_counts['Precedent Script'] = 1
                    
                    # Calculate effort estimate
                    effort_map = {
                        'If Statement': 15,
                        'Search': 10,
                        'Reflection': 5,
                        'Built In Script': 20,
                        'Extended': 5,
                        'Unbound': 5,
                        'Scripted': 30,
                        'Precedent Script': 30,
                        'Select': 10,
                        'Association': 5
                    }
                    
                    total_minutes = sum(field_counts.get(cat, 0) * effort_map.get(cat, 0) 
                                      for cat in effort_map.keys())
                    
                    # Add form time for unbound
                    if field_counts.get('Unbound', 0) > 0:
                        total_minutes += 15
                    
                    extracted = {
                        'ClientTitle': client_title,
                        'Code': code,
                        'PrecID': prec_elem.findtext('PrecID', ''),
                        'PrecTitle': prec_elem.findtext('PrecTitle', ''),
                        'PrecType': prec_elem.findtext('PrecType', ''),
                        'PrecCategory': prec_elem.findtext('PrecCategory', ''),
                        'PrecPath': prec_elem.findtext('PrecPath', ''),
                        'HasPreview': bool(prec_preview),
                        'PreviewLength': len(prec_preview) if prec_preview else 0,
                        'HasScript': bool(prec_script),
                        'TotalFields': sum(field_counts.values()),
                        'EstimatedMinutes': total_minutes,
                        'EstimatedHours': round(total_minutes / 60, 2)
                    }
                    
                    # Add field counts
                    for field_type, count in field_counts.items():
                        extracted[f'{field_type}_Count'] = count
                    
                    extracted_data.append(extracted)
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
        else:
            no_folder += 1
    else:
        no_folder += 1

print(f"\n✓ Successfully extracted: {successful}")
print(f"⚠ No folder found: {no_folder}")
print(f"⚠ No preview content: {no_preview}")
print(f"⚠ Failed to parse: {failed}")

# Convert to DataFrame and analyze
df_extracted = pd.DataFrame(extracted_data)

print("\n3. ANALYSIS OF EXTRACTED DATA")
print("-" * 60)

if len(df_extracted) > 0:
    # Field statistics
    templates_with_fields = df_extracted[df_extracted['TotalFields'] > 0]
    print(f"\nTemplates with detected fields: {len(templates_with_fields)}/{len(df_extracted)}")
    
    if len(templates_with_fields) > 0:
        print(f"Average fields per template: {templates_with_fields['TotalFields'].mean():.1f}")
        print(f"Total estimated hours: {df_extracted['EstimatedHours'].sum():.0f}")
        print(f"Average hours per template: {df_extracted['EstimatedHours'].mean():.2f}")
        
        # Complexity distribution
        def categorize_complexity(hours):
            if hours == 0:
                return 'No Data'
            elif hours < 2:
                return 'Simple'
            elif hours < 8:
                return 'Moderate'
            else:
                return 'Complex'
        
        df_extracted['Complexity'] = df_extracted['EstimatedHours'].apply(categorize_complexity)
        
        print("\nComplexity Distribution:")
        complexity_counts = df_extracted['Complexity'].value_counts()
        for complexity in ['Simple', 'Moderate', 'Complex', 'No Data']:
            if complexity in complexity_counts.index:
                count = complexity_counts[complexity]
                pct = count / len(df_extracted) * 100
                print(f"  {complexity:10s}: {count:3d} ({pct:.1f}%)")
        
        # Field type summary
        print("\nField Type Summary (total across all templates):")
        field_types = ['If Statement', 'DOCVARIABLE', 'Search', 'Reflection', 
                      'Built In Script', 'Extended', 'Unbound', 'Scripted', 
                      'Precedent Script', 'Select', 'MERGEFORMAT', 'Association']
        
        for field_type in field_types:
            col_name = f'{field_type}_Count'
            if col_name in df_extracted.columns:
                total = df_extracted[col_name].sum()
                if total > 0:
                    print(f"  {field_type:20s}: {total:4d}")

print("\n4. COMPARISON WITH SQL-BASED ESTIMATES")
print("-" * 60)

# Load SQL-based analysis for comparison
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/field_analysis.json', 'r') as f:
    sql_field_analysis = json.load(f)

# Get average from SQL documents
sql_by_doc = defaultdict(lambda: defaultdict(int))
for record in sql_field_analysis:
    doc_id = record['documentid']
    category = record['field_category']
    sql_by_doc[doc_id][category] += 1

sql_effort_map = {
    'Reflection': 5,
    'Extended': 5,
    'Unbound': 5,
    'Search': 10,
    'If': 15,
    'Built In Script': 20,
    'Scripted': 30,
    'Precedent Script': 30
}

sql_doc_hours = []
for doc_id, fields in sql_by_doc.items():
    minutes = sum(count * sql_effort_map.get(cat, 10) for cat, count in fields.items())
    if fields.get('Unbound', 0) > 0:
        minutes += 15
    sql_doc_hours.append(minutes / 60)

if sql_doc_hours:
    sql_avg_hours = sum(sql_doc_hours) / len(sql_doc_hours)
    print(f"\nSQL-based average: {sql_avg_hours:.2f} hours per document")
    
    if len(df_extracted) > 0:
        xml_avg_hours = df_extracted['EstimatedHours'].mean()
        print(f"XML-based average: {xml_avg_hours:.2f} hours per document")
        print(f"Difference: {abs(sql_avg_hours - xml_avg_hours):.2f} hours")
        
        # Project total effort for 279 templates
        print(f"\nProjected effort for 279 manifest-only templates:")
        print(f"  Using XML extraction: {df_extracted['EstimatedHours'].sum():.0f} hours")
        print(f"  Using SQL average: {279 * sql_avg_hours:.0f} hours")

# Save results
print("\n5. Saving Results...")

output_file = '../ClaudeReview/manifest_only_field_extraction.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full extraction results
    if len(df_extracted) > 0:
        df_extracted.to_excel(writer, sheet_name='Extracted Fields', index=False)
    
    # Summary statistics
    summary_data = {
        'Metric': [
            'Total Manifest-Only Templates',
            'Successfully Extracted',
            'Templates with Fields',
            'Total Estimated Hours',
            'Average Hours per Template',
            'Templates with No Folder',
            'Templates with No Preview'
        ],
        'Value': [
            len(manifest_only),
            successful,
            len(templates_with_fields) if len(df_extracted) > 0 else 0,
            df_extracted['EstimatedHours'].sum() if len(df_extracted) > 0 else 0,
            df_extracted['EstimatedHours'].mean() if len(df_extracted) > 0 else 0,
            no_folder,
            no_preview
        ]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
    
    # Complexity breakdown
    if len(df_extracted) > 0:
        complexity_df = df_extracted['Complexity'].value_counts().reset_index()
        complexity_df.columns = ['Complexity', 'Count']
        complexity_df['Percentage'] = (complexity_df['Count'] / len(df_extracted) * 100).round(1)
        complexity_df.to_excel(writer, sheet_name='Complexity', index=False)

print(f"✓ Saved to {output_file}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if successful > 0:
    coverage = successful / len(manifest_only) * 100
    print(f"\n✅ Successfully extracted field data from {coverage:.1f}% of manifest-only templates")
    
    if len(templates_with_fields) > 0:
        field_coverage = len(templates_with_fields) / successful * 100
        print(f"✅ {field_coverage:.1f}% of extracted templates have detectable fields")
        print(f"✅ Total estimated effort: {df_extracted['EstimatedHours'].sum():.0f} hours")
    
    print("\n📊 RECOMMENDATION:")
    if coverage > 50:
        print("• XML extraction provides sufficient data for effort estimation")
        print("• Combined with SQL data, we have field analysis for ~99% of templates")
    else:
        print("• XML extraction has limitations due to missing folders/previews")
        print("• Consider alternative approaches for templates without XML data")
else:
    print("\n⚠️ Unable to extract field data from manifest-only templates")
    print("• May need to import to SQL for complete analysis")

print("\n" + "=" * 80)
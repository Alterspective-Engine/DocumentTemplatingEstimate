import json
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

print("=" * 80)
print("COMPREHENSIVE ANALYSIS WITH NEW SQL DATA")
print("=" * 80)

# Load the new SQL data
print("\n1. Loading new SQL export data...")
sql_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL')

# Load documents
with open(sql_path / 'documents.json', 'r') as f:
    documents = json.load(f)
print(f"✓ Loaded {len(documents)} documents")

# Load fields
with open(sql_path / 'fields.json', 'r') as f:
    fields = json.load(f)
print(f"✓ Loaded {len(fields)} fields")

# Load document-field mappings
with open(sql_path / 'documentfields.json', 'r') as f:
    doc_fields = json.load(f)
print(f"✓ Loaded {len(doc_fields)} document-field mappings")

# Load the categorized field analysis
with open(sql_path / 'field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ Loaded {len(field_analysis)} categorized field analyses")

# Build document lookup
doc_lookup = {}
doc_lookup_by_id = {}
for doc in documents:
    doc_id = doc['DocumentID']
    filename = doc['Filename']
    if filename:
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        doc_lookup[basename] = doc
        doc_lookup_by_id[doc_id] = doc

print(f"✓ Built lookup for {len(doc_lookup)} documents")

# Load Client Requirements
print("\n2. Loading Client Requirements...")
df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
print(f"✓ Loaded {len(df_client)} client requirements")

# Load manifest for code mapping
print("\n3. Building code mapping from manifest...")
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

code_to_info = {}
name_to_code = {}

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
        code_to_info[code] = {
            'Name': name,
            'PrecTitle': prec_title,
            'Description': description
        }
        
        if name:
            name_to_code[name.lower()] = code
        if prec_title:
            name_to_code[prec_title.lower()] = code

print(f"✓ Found {len(code_to_info)} precedent codes in manifest")

# Analyze field categories from the new data
print("\n4. Analyzing field categories...")
category_counts = defaultdict(int)
doc_field_profiles = defaultdict(lambda: defaultdict(int))

for record in field_analysis:
    doc_id = record['documentid']
    category = record['field_category']
    
    category_counts[category] += 1
    doc_field_profiles[doc_id][category] += 1
    doc_field_profiles[doc_id]['Total'] += 1

print("\nField Category Distribution:")
for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category:20s}: {count:,} instances")

# Effort estimates from BecInfo
effort_minutes = {
    'Reflection': 5,
    'Extended': 5,
    'Unbound': 5,  # Plus 15 for form creation
    'Search': 10,
    'If': 15,  # Note: shortened from "If Statement"
    'Built In Script': 20,
    'Scripted': 30,
    'Precedent Script': 30
}

# Match client requirements with documents
print("\n5. Matching Client Requirements with SQL data...")
comprehensive_data = []
matched_direct = 0
matched_via_code = 0
no_match = 0

for idx, row in df_client.iterrows():
    title = row['Current Title']
    title_lower = title.lower()
    
    result = {
        'ClientTitle': title,
        'Description': row['Description'],
        'OriginalComplexity': row['Complexity'],
        'MappedCode': None,
        'HasSQLData': False,
        'DocumentID': None,
        'Filename': None,
        'TotalFields': 0,
        'EstimatedMinutes': 0,
        'EstimatedHours': 0,
        'MatchType': 'No Match'
    }
    
    # Initialize category columns
    for category in effort_minutes.keys():
        result[f'{category}_Count'] = 0
        result[f'{category}_Minutes'] = 0
    
    # First try direct match
    if title_lower in doc_lookup:
        matched_direct += 1
        doc = doc_lookup[title_lower]
        doc_id = doc['DocumentID']
        result['HasSQLData'] = True
        result['DocumentID'] = doc_id
        result['Filename'] = doc['Filename']
        result['MatchType'] = 'Direct Match'
    else:
        # Try via code mapping
        code = name_to_code.get(title_lower)
        if code and code in doc_lookup:
            matched_via_code += 1
            doc = doc_lookup[code]
            doc_id = doc['DocumentID']
            result['MappedCode'] = code
            result['HasSQLData'] = True
            result['DocumentID'] = doc_id
            result['Filename'] = doc['Filename']
            result['MatchType'] = 'Matched via Code'
        else:
            no_match += 1
    
    # If we have a match, get field details
    if result['HasSQLData'] and result['DocumentID'] in doc_field_profiles:
        profile = doc_field_profiles[result['DocumentID']]
        result['TotalFields'] = profile['Total']
        
        total_minutes = 0
        for category, minutes_per in effort_minutes.items():
            count = profile.get(category, 0)
            result[f'{category}_Count'] = count
            category_minutes = count * minutes_per
            result[f'{category}_Minutes'] = category_minutes
            total_minutes += category_minutes
        
        # Add form creation time for unbound fields
        if profile.get('Unbound', 0) > 0:
            total_minutes += 15
        
        result['EstimatedMinutes'] = total_minutes
        result['EstimatedHours'] = round(total_minutes / 60, 2)
    
    comprehensive_data.append(result)

# Convert to DataFrame
df_comprehensive = pd.DataFrame(comprehensive_data)

# Calculate complexity
def calculate_complexity(hours):
    if hours == 0:
        return 'No Data'
    elif hours < 2:
        return 'Simple'
    elif hours < 8:
        return 'Moderate'
    else:
        return 'Complex'

df_comprehensive['CalculatedComplexity'] = df_comprehensive['EstimatedHours'].apply(calculate_complexity)

# Generate statistics
print("\n" + "=" * 80)
print("ANALYSIS RESULTS")
print("=" * 80)

print(f"\nMatching Statistics:")
print(f"  Total client requirements: {len(df_client)}")
print(f"  Direct matches: {matched_direct} ({matched_direct/len(df_client)*100:.1f}%)")
print(f"  Matched via code: {matched_via_code} ({matched_via_code/len(df_client)*100:.1f}%)")
print(f"  Total matched: {matched_direct + matched_via_code} ({(matched_direct + matched_via_code)/len(df_client)*100:.1f}%)")
print(f"  No match: {no_match} ({no_match/len(df_client)*100:.1f}%)")

# Analyze matched documents
docs_with_data = df_comprehensive[df_comprehensive['HasSQLData'] == True]
docs_with_fields = docs_with_data[docs_with_data['TotalFields'] > 0]

if len(docs_with_fields) > 0:
    print(f"\nFor {len(docs_with_fields)} documents with field data:")
    print(f"  Average estimated hours: {docs_with_fields['EstimatedHours'].mean():.2f}")
    print(f"  Min estimated hours: {docs_with_fields['EstimatedHours'].min():.2f}")
    print(f"  Max estimated hours: {docs_with_fields['EstimatedHours'].max():.2f}")
    print(f"  Total estimated hours: {docs_with_fields['EstimatedHours'].sum():.0f}")
    
    print(f"\nComplexity Distribution:")
    for complexity in ['Simple', 'Moderate', 'Complex', 'No Data']:
        count = len(docs_with_fields[docs_with_fields['CalculatedComplexity'] == complexity])
        pct = count/len(docs_with_fields)*100 if len(docs_with_fields) > 0 else 0
        print(f"  {complexity:10s}: {count:3d} ({pct:.1f}%)")

print(f"\nField Category Totals (matched documents):")
total_by_category = defaultdict(int)
for category in effort_minutes.keys():
    col_name = f'{category}_Count'
    if col_name in docs_with_data.columns:
        total = docs_with_data[col_name].sum()
        total_by_category[category] = total
        if total > 0:
            hours = docs_with_data[f'{category}_Minutes'].sum() / 60
            print(f"  {category:20s}: {total:,} instances = {hours:.0f} hours")

# Save results
print("\n6. Saving comprehensive analysis...")
output_file = '../ClaudeReview/COMPLETE_EstimateDoc_Analysis.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Full analysis
    df_comprehensive.to_excel(writer, sheet_name='Full Analysis', index=False)
    
    # Summary statistics
    summary_data = {
        'Metric': [
            'Total Client Requirements',
            'Direct Matches',
            'Matched via Code',
            'Total Matched',
            'Match Rate',
            'No Match',
            'Documents with Field Data',
            'Average Hours per Document',
            'Total Estimated Hours'
        ],
        'Value': [
            len(df_client),
            matched_direct,
            matched_via_code,
            matched_direct + matched_via_code,
            f"{(matched_direct + matched_via_code)/len(df_client)*100:.1f}%",
            no_match,
            len(docs_with_fields),
            f"{docs_with_fields['EstimatedHours'].mean():.2f}" if len(docs_with_fields) > 0 else "0",
            f"{docs_with_fields['EstimatedHours'].sum():.0f}" if len(docs_with_fields) > 0 else "0"
        ]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
    
    # Field category analysis
    category_analysis = []
    for category, count in sorted(total_by_category.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            minutes = effort_minutes.get(category, 0)
            total_hours = (count * minutes) / 60
            category_analysis.append({
                'Category': category,
                'Total Instances': count,
                'Minutes per Instance': minutes,
                'Total Hours': round(total_hours, 1)
            })
    pd.DataFrame(category_analysis).to_excel(writer, sheet_name='Field Categories', index=False)
    
    # Complexity breakdown
    complexity_breakdown = []
    for complexity in ['Simple', 'Moderate', 'Complex']:
        complex_docs = docs_with_fields[docs_with_fields['CalculatedComplexity'] == complexity]
        if len(complex_docs) > 0:
            complexity_breakdown.append({
                'Complexity': complexity,
                'Count': len(complex_docs),
                'Percentage': f"{len(complex_docs)/len(docs_with_fields)*100:.1f}%",
                'Avg Hours': complex_docs['EstimatedHours'].mean(),
                'Total Hours': complex_docs['EstimatedHours'].sum()
            })
    pd.DataFrame(complexity_breakdown).to_excel(writer, sheet_name='Complexity Analysis', index=False)

print(f"✓ Saved to {output_file}")

# Also save a JSON summary
summary_json = {
    'analysis_date': pd.Timestamp.now().isoformat(),
    'data_source': 'New SQL Export (newSQL directory)',
    'matching_stats': {
        'total_requirements': len(df_client),
        'direct_matches': matched_direct,
        'code_matches': matched_via_code,
        'total_matched': matched_direct + matched_via_code,
        'match_rate': f"{(matched_direct + matched_via_code)/len(df_client)*100:.1f}%"
    },
    'effort_summary': {
        'total_hours': docs_with_fields['EstimatedHours'].sum() if len(docs_with_fields) > 0 else 0,
        'average_hours': docs_with_fields['EstimatedHours'].mean() if len(docs_with_fields) > 0 else 0,
        'documents_with_data': len(docs_with_fields)
    },
    'field_categories': dict(category_counts),
    'complexity_distribution': complexity_breakdown
}

with open('../ClaudeReview/complete_analysis_summary.json', 'w') as f:
    json.dump(summary_json, f, indent=2, default=str)

print("✓ Saved JSON summary")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
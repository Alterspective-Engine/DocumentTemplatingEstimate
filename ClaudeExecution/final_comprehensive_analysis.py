import xml.etree.ElementTree as ET
import pymssql
import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("FINAL COMPREHENSIVE ANALYSIS WITH CORRECT MAPPING")
print("=" * 80)

# Database connection
server = 'mosmar-cip.database.windows.net'
database = 'Mosmar_CIP_Dev'
username = 'mosmaradmin'
password = 'M0sM4r.2021'

conn = pymssql.connect(
    server=server,
    user=username,
    password=password,
    database=database,
    tds_version='7.4'
)
cursor = conn.cursor()

print("\n1. Building Code Mapping from Manifest...")
# Load the manifest to get code mappings
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

# Build comprehensive mapping
code_to_info = {}
name_to_code = {}

for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    # Extract PrecTitle from description
    prec_title = None
    desc_lines = description.split('\n')
    for i, line in enumerate(desc_lines):
        if i == 2:  # Third line
            prec_title = line.strip()
            break
    
    if code:
        code_to_info[code] = {
            'Name': name,
            'PrecTitle': prec_title,
            'Description': description
        }
        
        # Create reverse mappings
        if name:
            name_to_code[name.lower()] = code
        if prec_title:
            name_to_code[prec_title.lower()] = code

print(f"✓ Found {len(code_to_info)} precedent codes in manifest")

print("\n2. Loading Client Requirements...")
df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
print(f"✓ Loaded {len(df_client)} client requirements")

print("\n3. Getting All Documents from Database...")
cursor.execute("SELECT DocumentID, Filename FROM dbo.Documents")
all_docs = cursor.fetchall()
sql_docs_by_filename = {doc[1]: doc[0] for doc in all_docs if doc[1]}
sql_docs_by_basename = {}
for filename, doc_id in sql_docs_by_filename.items():
    basename = filename.replace('.dot', '').replace('.docx', '')
    sql_docs_by_basename[basename] = doc_id

print(f"✓ Retrieved {len(all_docs)} documents from database")

print("\n4. Getting Field Data with Correct Categories...")
# Use the query from BecInfo with fixed escape character
cursor.execute("""
    SELECT
        DOC.DocumentID,
        DOC.Filename,
        F.FieldID,
        F.FieldCode,
        DF.Count,
        CASE
            WHEN F.FieldCode LIKE '%UDSCH%' THEN 'Search'
            WHEN F.FieldCode LIKE '%~%' THEN 'Reflection'
            WHEN F.FieldCode LIKE '%IF%' THEN 'If Statement'
            WHEN F.FieldCode LIKE '%DOCVARIABLE "#%' THEN 'Built In Script'
            WHEN F.FieldCode LIKE '%$$%' THEN 'Extended'
            WHEN F.FieldCode LIKE '%SCR%' THEN 'Scripted'
            WHEN F.FieldCode LIKE '%[_]%' THEN 'Unbound'
            ELSE 'Precedent Script'
        END AS field_category
    FROM
        Documents DOC
    INNER JOIN
        DocumentFields DF ON DOC.DocumentID = DF.DocumentID
    INNER JOIN
        Fields F ON F.FieldID = DF.FieldID
""")

all_field_data = cursor.fetchall()
print(f"✓ Retrieved {len(all_field_data)} field mappings")

# Build document field profiles
doc_field_profiles = defaultdict(lambda: defaultdict(int))
field_categories_used = set()

for row in all_field_data:
    doc_id = row[0]
    field_id = row[2]
    count = row[4] or 1
    category = row[5]
    
    field_categories_used.add(category)
    doc_field_profiles[doc_id][category] += count
    doc_field_profiles[doc_id]['Total'] += count
    doc_field_profiles[doc_id]['UniqueFields'] += 1

print(f"✓ Processed field data for {len(doc_field_profiles)} documents")

# Effort estimates from BecInfo
effort_minutes = {
    'Reflection': 5,
    'Extended': 5,
    'Unbound': 5,  # Plus 15 for form creation
    'Search': 10,
    'If Statement': 15,
    'Built In Script': 20,
    'Scripted': 30,
    'Precedent Script': 30
}

print("\n5. Matching Client Requirements with Database...")
comprehensive_data = []
matched_count = 0
no_code_count = 0
code_not_in_sql_count = 0

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
        'TotalFieldInstances': 0,
        'UniqueFields': 0,
        'EstimatedMinutes': 0,
        'EstimatedHours': 0,
        'MatchStatus': 'Not Matched'
    }
    
    # Initialize category columns
    for category in effort_minutes.keys():
        result[f'{category}_Count'] = 0
        result[f'{category}_Minutes'] = 0
    
    # Try to find code for this title
    code = name_to_code.get(title_lower)
    
    if code:
        result['MappedCode'] = code
        
        # Check if this code exists in SQL database
        if code in sql_docs_by_basename:
            matched_count += 1
            doc_id = sql_docs_by_basename[code]
            result['HasSQLData'] = True
            result['DocumentID'] = doc_id
            result['Filename'] = f"{code}.dot"
            result['MatchStatus'] = 'Matched'
            
            # Get field profile
            if doc_id in doc_field_profiles:
                profile = doc_field_profiles[doc_id]
                result['TotalFieldInstances'] = profile['Total']
                result['UniqueFields'] = profile['UniqueFields']
                
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
        else:
            code_not_in_sql_count += 1
            result['MatchStatus'] = 'Code Not in SQL'
    else:
        no_code_count += 1
        result['MatchStatus'] = 'No Code Mapping'
    
    comprehensive_data.append(result)

# Convert to DataFrame
df_comprehensive = pd.DataFrame(comprehensive_data)

# Calculate complexity based on estimated hours
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

print("\n" + "=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)

print(f"\nMatching Statistics:")
print(f"  Total client requirements: {len(df_client)}")
print(f"  Successfully matched with SQL data: {matched_count} ({matched_count/len(df_client)*100:.1f}%)")
print(f"  Has code but not in SQL: {code_not_in_sql_count} ({code_not_in_sql_count/len(df_client)*100:.1f}%)")
print(f"  No code mapping found: {no_code_count} ({no_code_count/len(df_client)*100:.1f}%)")

docs_with_data = df_comprehensive[df_comprehensive['HasSQLData'] == True]
if len(docs_with_data) > 0:
    print(f"\nFor {len(docs_with_data)} documents with field data:")
    print(f"  Average estimated hours: {docs_with_data['EstimatedHours'].mean():.2f}")
    print(f"  Min estimated hours: {docs_with_data['EstimatedHours'].min():.2f}")
    print(f"  Max estimated hours: {docs_with_data['EstimatedHours'].max():.2f}")
    print(f"  Total estimated hours: {docs_with_data['EstimatedHours'].sum():.2f}")

print(f"\nComplexity Distribution (for matched documents):")
complexity_dist = docs_with_data['CalculatedComplexity'].value_counts() if len(docs_with_data) > 0 else pd.Series()
for complexity in ['Simple', 'Moderate', 'Complex']:
    count = complexity_dist.get(complexity, 0)
    pct = count/len(docs_with_data)*100 if len(docs_with_data) > 0 else 0
    print(f"  {complexity}: {count} ({pct:.1f}%)")

print(f"\nField Category Totals (across all matched documents):")
for category in sorted(effort_minutes.keys()):
    col_name = f'{category}_Count'
    if col_name in docs_with_data.columns:
        total = docs_with_data[col_name].sum()
        if total > 0:
            print(f"  {category:20s}: {total:,} instances")

# Save comprehensive analysis
print("\n6. Saving Results...")
output_file = '../ClaudeReview/FINAL_EstimateDoc_Analysis.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main analysis sheet
    df_comprehensive.to_excel(writer, sheet_name='Full Analysis', index=False)
    
    # Summary statistics
    summary_data = {
        'Metric': [
            'Total Client Requirements',
            'Successfully Matched',
            'Match Rate',
            'Has Code but Not in SQL',
            'No Code Mapping',
            'Average Hours (Matched)',
            'Total Hours (Matched)',
            'Documents with Field Data'
        ],
        'Value': [
            len(df_client),
            matched_count,
            f"{matched_count/len(df_client)*100:.1f}%",
            code_not_in_sql_count,
            no_code_count,
            f"{docs_with_data['EstimatedHours'].mean():.2f}" if len(docs_with_data) > 0 else "0",
            f"{docs_with_data['EstimatedHours'].sum():.2f}" if len(docs_with_data) > 0 else "0",
            len(doc_field_profiles)
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    df_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Field categories with effort
    category_data = []
    for category in sorted(effort_minutes.keys()):
        col_name = f'{category}_Count'
        if col_name in docs_with_data.columns:
            total_instances = docs_with_data[col_name].sum()
            total_minutes = docs_with_data[f'{category}_Minutes'].sum()
            category_data.append({
                'Category': category,
                'Total Instances': total_instances,
                'Minutes per Instance': effort_minutes[category],
                'Total Minutes': total_minutes,
                'Total Hours': round(total_minutes/60, 2)
            })
    df_categories = pd.DataFrame(category_data)
    df_categories.to_excel(writer, sheet_name='Field Categories', index=False)
    
    # Complexity distribution
    if len(docs_with_data) > 0:
        complexity_analysis = []
        for complexity in ['Simple', 'Moderate', 'Complex']:
            docs = docs_with_data[docs_with_data['CalculatedComplexity'] == complexity]
            complexity_analysis.append({
                'Complexity': complexity,
                'Count': len(docs),
                'Percentage': f"{len(docs)/len(docs_with_data)*100:.1f}%",
                'Avg Hours': f"{docs['EstimatedHours'].mean():.2f}" if len(docs) > 0 else "0",
                'Total Hours': f"{docs['EstimatedHours'].sum():.2f}" if len(docs) > 0 else "0"
            })
        df_complexity = pd.DataFrame(complexity_analysis)
        df_complexity.to_excel(writer, sheet_name='Complexity Analysis', index=False)

print(f"✓ Saved comprehensive analysis to {output_file}")

# Save JSON summary
json_summary = {
    'analysis_date': pd.Timestamp.now().isoformat(),
    'matching_statistics': {
        'total_client_requirements': len(df_client),
        'successfully_matched': matched_count,
        'match_rate': f"{matched_count/len(df_client)*100:.1f}%",
        'code_not_in_sql': code_not_in_sql_count,
        'no_code_mapping': no_code_count
    },
    'effort_estimates': {
        'total_hours': docs_with_data['EstimatedHours'].sum() if len(docs_with_data) > 0 else 0,
        'average_hours': docs_with_data['EstimatedHours'].mean() if len(docs_with_data) > 0 else 0,
        'by_category': category_data
    },
    'complexity_distribution': complexity_analysis if len(docs_with_data) > 0 else []
}

with open('../ClaudeReview/final_analysis_summary.json', 'w') as f:
    json.dump(json_summary, f, indent=2, default=str)

print("✓ Saved summary to final_analysis_summary.json")

conn.close()

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
print(f"\n✓ Successfully analyzed {matched_count} documents with field-level detail")
print(f"✓ Total estimated effort: {docs_with_data['EstimatedHours'].sum():.0f} hours")
print(f"✓ Results saved to ClaudeReview folder")
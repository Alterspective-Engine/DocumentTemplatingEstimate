import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

print("=" * 80)
print("ANALYZING THE 336 MATCHED DOCUMENTS - FIELD REUSABILITY")
print("=" * 80)

# Load data
print("\n1. Loading data sources...")

# Load the ultimate mapping to get the 336 matched documents
df_mapping = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ClaudeReview/ULTIMATE_Mapping_Solution.xlsx')
matched_336 = df_mapping[df_mapping['SQLDocID'].notna()].copy()
print(f"✓ Found {len(matched_336)} documents with SQL data")

# Load field analysis
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ Loaded {len(field_analysis)} field analysis records")

# Load documents for additional info
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)
doc_by_id = {d['DocumentID']: d for d in sql_documents}

print("\n2. Analyzing field patterns and reusability...")

# Build comprehensive field data structures
fields_by_doc = defaultdict(lambda: defaultdict(list))
field_occurrence = defaultdict(lambda: defaultdict(set))  # field_code -> category -> set of doc_ids
all_field_codes = defaultdict(set)  # category -> set of all unique field codes

# Process all field analysis records
for record in field_analysis:
    doc_id = record['documentid']
    field_code = record.get('fieldcode', '') or ''
    field_code = field_code.strip() if field_code else ''
    field_result = record.get('fieldresult', '') or ''
    field_result = field_result.strip() if field_result else ''
    category = record.get('field_category', 'Unknown')
    
    # Store field for this document
    if field_code:
        fields_by_doc[doc_id][category].append(field_code)
        # Track which documents use this field
        field_occurrence[field_code][category].add(doc_id)
        all_field_codes[category].add(field_code)

print(f"✓ Processed fields for {len(fields_by_doc)} documents")

# Analyze reusability for each field
field_reusability = {}
for field_code, categories in field_occurrence.items():
    for category, doc_ids in categories.items():
        usage_count = len(doc_ids)
        reusability = "Unique" if usage_count == 1 else f"Shared ({usage_count} docs)"
        field_reusability[(field_code, category)] = {
            'usage_count': usage_count,
            'is_unique': usage_count == 1,
            'is_reusable': usage_count > 1,
            'reusability_label': reusability
        }

print(f"✓ Analyzed reusability for {len(field_reusability)} field-category combinations")

# Build the 336 document analysis
print("\n3. Building detailed analysis for the 336 matched documents...")

results = []
categories = ['If', 'Precedent Script', 'Reflection', 'Search', 'Unbound', 
              'Built In Script', 'Extended', 'Scripted']

for idx, row in matched_336.iterrows():
    doc_id = int(row['SQLDocID'])
    
    result = {
        'ClientTitle': row['ClientTitle'],
        'SQLDocID': doc_id,
        'SQLFilename': row['SQLFilename'],
        'TotalFields': row.get('TotalFields', 0),
        'EstimatedHours': row.get('EstimatedHours', 0)
    }
    
    # Get document metadata
    if doc_id in doc_by_id:
        doc = doc_by_id[doc_id]
        result['Sections'] = doc.get('Sections', 0)
        result['Tables'] = doc.get('Tables', 0)
        result['Checkboxes'] = doc.get('Checkboxes', 0)
    
    # Analyze fields by category
    doc_fields = fields_by_doc.get(doc_id, {})
    
    for category in categories:
        cat_fields = doc_fields.get(category, [])
        total_count = len(cat_fields)
        
        # Count unique vs reusable
        unique_count = 0
        reusable_count = 0
        
        for field_code in cat_fields:
            reuse_info = field_reusability.get((field_code, category), {})
            if reuse_info.get('is_unique', False):
                unique_count += 1
            else:
                reusable_count += 1
        
        # Add to result
        result[f'{category}_Total'] = total_count
        result[f'{category}_Unique'] = unique_count
        result[f'{category}_Reusable'] = reusable_count
        result[f'{category}_UniqueRatio'] = f"{(unique_count/total_count*100):.1f}%" if total_count > 0 else "N/A"
    
    # Calculate overall uniqueness
    total_all_fields = sum(len(fields) for fields in doc_fields.values())
    total_unique_fields = sum(
        1 for cat in doc_fields.values() 
        for field in cat 
        if field_reusability.get((field, category), {}).get('is_unique', False)
    )
    
    result['Total_All_Fields'] = total_all_fields
    result['Total_Unique_Fields'] = total_unique_fields
    result['Overall_Unique_Ratio'] = f"{(total_unique_fields/total_all_fields*100):.1f}%" if total_all_fields > 0 else "N/A"
    
    results.append(result)

df_results = pd.DataFrame(results)

print(f"✓ Analyzed {len(df_results)} documents")

# Calculate summary statistics
print("\n4. Calculating summary statistics...")

summary_stats = []
for category in categories:
    total_col = f'{category}_Total'
    unique_col = f'{category}_Unique'
    reusable_col = f'{category}_Reusable'
    
    if total_col in df_results.columns:
        total_sum = df_results[total_col].sum()
        unique_sum = df_results[unique_col].sum()
        reusable_sum = df_results[reusable_col].sum()
        
        # Count how many unique field codes exist in this category
        unique_field_codes = len([
            field for field, cat in field_reusability.keys() 
            if cat == category and field_reusability[(field, cat)]['is_unique']
        ])
        
        total_field_codes = len(all_field_codes.get(category, set()))
        
        summary_stats.append({
            'Category': category,
            'Total_Instances': total_sum,
            'Unique_Instances': unique_sum,
            'Reusable_Instances': reusable_sum,
            'Unique_Ratio': f"{(unique_sum/total_sum*100):.1f}%" if total_sum > 0 else "N/A",
            'Unique_Field_Codes': unique_field_codes,
            'Total_Field_Codes': total_field_codes,
            'Reusability_Potential': f"{(reusable_sum/total_sum*100):.1f}%" if total_sum > 0 else "N/A"
        })

df_summary = pd.DataFrame(summary_stats)

# Find most commonly reused fields
print("\n5. Identifying most commonly reused fields...")

def clean_field_code(code):
    """Remove illegal characters for Excel"""
    if not code:
        return ""
    # Remove control characters
    cleaned = ''.join(char if ord(char) >= 32 else ' ' for char in code)
    # Truncate if too long
    return cleaned[:100]

reused_fields = []
for (field_code, category), info in field_reusability.items():
    if info['usage_count'] > 1:
        reused_fields.append({
            'Field_Code': clean_field_code(field_code),  # Clean and truncate
            'Category': category,
            'Usage_Count': info['usage_count'],
            'Reusability': f"Used in {info['usage_count']} documents"
        })

df_reused = pd.DataFrame(reused_fields)
if len(df_reused) > 0:
    df_reused = df_reused.sort_values('Usage_Count', ascending=False)

# Save everything to Excel
print("\n6. Saving results to Excel...")

output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/The336_Field_Analysis.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main analysis - 336 documents
    df_results.to_excel(writer, sheet_name='336_Documents', index=False)
    
    # Summary statistics
    df_summary.to_excel(writer, sheet_name='Summary_By_Category', index=False)
    
    # Top reused fields
    if len(df_reused) > 0:
        df_reused.head(100).to_excel(writer, sheet_name='Top_Reused_Fields', index=False)
    
    # Category breakdown
    category_analysis = []
    for category in categories:
        cat_data = {
            'Category': category,
            'Documents_With_Fields': sum(df_results[f'{category}_Total'] > 0),
            'Avg_Fields_Per_Doc': df_results[df_results[f'{category}_Total'] > 0][f'{category}_Total'].mean() if any(df_results[f'{category}_Total'] > 0) else 0,
            'Max_Fields_In_Doc': df_results[f'{category}_Total'].max(),
            'Total_Unique_Codes': len([f for f, c in field_reusability.keys() if c == category and field_reusability[(f, c)]['is_unique']]),
            'Total_Reusable_Codes': len([f for f, c in field_reusability.keys() if c == category and field_reusability[(f, c)]['usage_count'] > 1])
        }
        category_analysis.append(cat_data)
    
    pd.DataFrame(category_analysis).to_excel(writer, sheet_name='Category_Analysis', index=False)
    
    # Document complexity ranking
    df_complexity = df_results[['ClientTitle', 'SQLFilename', 'Total_All_Fields', 'Total_Unique_Fields', 'EstimatedHours']].copy()
    df_complexity['Uniqueness_Score'] = df_results['Total_Unique_Fields'] / df_results['Total_All_Fields']
    df_complexity = df_complexity.sort_values('Total_Unique_Fields', ascending=False)
    df_complexity.head(50).to_excel(writer, sheet_name='Most_Unique_Documents', index=False)

print(f"✓ Saved to {output_file}")

# Print key findings
print("\n" + "=" * 80)
print("KEY FINDINGS")
print("=" * 80)

print("\n1. OVERALL REUSABILITY:")
total_instances = df_summary['Total_Instances'].sum()
unique_instances = df_summary['Unique_Instances'].sum()
reusable_instances = df_summary['Reusable_Instances'].sum()

print(f"   Total field instances: {total_instances:,}")
print(f"   Unique instances: {unique_instances:,} ({unique_instances/total_instances*100:.1f}%)")
print(f"   Reusable instances: {reusable_instances:,} ({reusable_instances/total_instances*100:.1f}%)")

print("\n2. REUSABILITY BY CATEGORY:")
for idx, row in df_summary.iterrows():
    if row['Total_Instances'] > 0:
        print(f"   {row['Category']:20s}: {row['Reusability_Potential']:>6s} reusable ({row['Reusable_Instances']:,} of {row['Total_Instances']:,})")

print("\n3. TOP REUSED FIELDS:")
if len(df_reused) > 0:
    for idx, row in df_reused.head(10).iterrows():
        print(f"   {row['Category']:20s}: Used in {row['Usage_Count']} documents")

print("\n4. OPTIMIZATION POTENTIAL:")
print(f"   • {reusable_instances/total_instances*100:.1f}% of fields are already reused")
print(f"   • Creating common components for reused fields could save significant effort")
print(f"   • Focus on categories with high reusability: If statements and Precedent Scripts")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
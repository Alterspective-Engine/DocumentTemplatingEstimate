import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

print("=" * 80)
print("ANALYZING THE 336 MATCHED DOCUMENTS - FIELD REUSABILITY (IMPROVED)")
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
field_occurrence = defaultdict(lambda: defaultdict(set))
all_field_codes = defaultdict(set)

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
        field_occurrence[field_code][category].add(doc_id)
        all_field_codes[category].add(field_code)

print(f"✓ Processed fields for {len(fields_by_doc)} documents")

# Analyze reusability
field_reusability = {}
for field_code, categories in field_occurrence.items():
    for category, doc_ids in categories.items():
        usage_count = len(doc_ids)
        field_reusability[(field_code, category)] = {
            'usage_count': usage_count,
            'is_unique': usage_count == 1,
            'is_reusable': usage_count > 1,
            'reusability_score': min(usage_count / 10, 1.0)  # Score 0-1 based on usage
        }

print(f"✓ Analyzed reusability for {len(field_reusability)} field-category combinations")

# Calculate effort estimates
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

print("\n3. Building detailed analysis for the 336 matched documents...")

results = []
categories = ['If', 'Precedent Script', 'Reflection', 'Search', 'Unbound', 
              'Built In Script', 'Extended', 'Scripted']

for idx, row in matched_336.iterrows():
    doc_id = int(row['SQLDocID'])
    
    result = {
        'ClientTitle': row['ClientTitle'],
        'ClientDescription': row.get('ClientDescription', ''),
        'SQLDocID': doc_id,
        'SQLFilename': row['SQLFilename'],
        'MatchStrategy': row.get('MatchStrategy', ''),
        'EstimatedHours': row.get('EstimatedHours', 0)
    }
    
    # Get document metadata
    if doc_id in doc_by_id:
        doc = doc_by_id[doc_id]
        result['Sections'] = doc.get('Sections', 0)
        result['Tables'] = doc.get('Tables', 0)
        result['Checkboxes'] = doc.get('Checkboxes', 0)
        result['SEQFields'] = doc.get('SEQFields', 0)
        result['REFFields'] = doc.get('REFFields', 0)
    else:
        result['Sections'] = 0
        result['Tables'] = 0
        result['Checkboxes'] = 0
        result['SEQFields'] = 0
        result['REFFields'] = 0
    
    # Analyze fields by category
    doc_fields = fields_by_doc.get(doc_id, {})
    
    # Calculate totals first
    total_all_fields = 0
    total_unique_fields = 0
    total_reusable_fields = 0
    total_effort_minutes = 0
    
    for category in categories:
        cat_fields = doc_fields.get(category, [])
        total_count = len(cat_fields)
        
        # Count unique vs reusable
        unique_count = 0
        reusable_count = 0
        category_effort = 0
        
        for field_code in cat_fields:
            reuse_info = field_reusability.get((field_code, category), {})
            if reuse_info.get('is_unique', False):
                unique_count += 1
            else:
                reusable_count += 1
            
            # Calculate effort for this field
            minutes_per = effort_map.get(category, 10)
            category_effort += minutes_per
        
        # Add to result with proper formatting
        result[f'{category}_Total'] = total_count
        result[f'{category}_Unique'] = unique_count
        result[f'{category}_Reusable'] = reusable_count
        
        # Calculate ratio - use 0 instead of N/A for empty categories
        if total_count > 0:
            result[f'{category}_UniqueRatio'] = round((unique_count/total_count) * 100, 1)
            result[f'{category}_ReusableRatio'] = round((reusable_count/total_count) * 100, 1)
        else:
            result[f'{category}_UniqueRatio'] = 0
            result[f'{category}_ReusableRatio'] = 0
        
        result[f'{category}_EstMinutes'] = category_effort
        
        # Add to totals
        total_all_fields += total_count
        total_unique_fields += unique_count
        total_reusable_fields += reusable_count
        total_effort_minutes += category_effort
    
    # Add special time for unbound forms
    if doc_fields.get('Unbound'):
        total_effort_minutes += 15
    
    # Overall statistics
    result['Total_All_Fields'] = total_all_fields
    result['Total_Unique_Fields'] = total_unique_fields
    result['Total_Reusable_Fields'] = total_reusable_fields
    
    # Calculate overall ratios
    if total_all_fields > 0:
        result['Overall_Unique_Ratio'] = round((total_unique_fields/total_all_fields) * 100, 1)
        result['Overall_Reusable_Ratio'] = round((total_reusable_fields/total_all_fields) * 100, 1)
    else:
        result['Overall_Unique_Ratio'] = 0
        result['Overall_Reusable_Ratio'] = 0
    
    # Effort calculations
    result['Calculated_Hours'] = round(total_effort_minutes / 60, 2)
    result['Original_Est_Hours'] = row.get('EstimatedHours', 0)
    result['Hours_Difference'] = round(result['Calculated_Hours'] - result['Original_Est_Hours'], 2)
    
    # Complexity scoring
    complexity_score = 0
    if total_all_fields > 50:
        complexity_score += 3
    elif total_all_fields > 25:
        complexity_score += 2
    elif total_all_fields > 10:
        complexity_score += 1
    
    if result['Overall_Unique_Ratio'] > 50:
        complexity_score += 3
    elif result['Overall_Unique_Ratio'] > 25:
        complexity_score += 2
    elif result['Overall_Unique_Ratio'] > 10:
        complexity_score += 1
    
    if result['Calculated_Hours'] > 20:
        complexity_score += 3
    elif result['Calculated_Hours'] > 10:
        complexity_score += 2
    elif result['Calculated_Hours'] > 5:
        complexity_score += 1
    
    # Assign complexity level
    if complexity_score >= 7:
        result['Complexity_Level'] = 'Very High'
    elif complexity_score >= 5:
        result['Complexity_Level'] = 'High'
    elif complexity_score >= 3:
        result['Complexity_Level'] = 'Medium'
    elif complexity_score >= 1:
        result['Complexity_Level'] = 'Low'
    else:
        result['Complexity_Level'] = 'Very Low'
    
    result['Complexity_Score'] = complexity_score
    
    # Optimization potential
    if total_reusable_fields > 0:
        # Calculate potential savings (30% reduction for reusable fields)
        reusable_minutes = sum(
            effort_map.get(cat, 10) * len([f for f in doc_fields.get(cat, []) 
            if not field_reusability.get((f, cat), {}).get('is_unique', False)])
            for cat in categories
        )
        potential_savings_hours = round((reusable_minutes * 0.3) / 60, 2)
        result['Optimization_Potential_Hours'] = potential_savings_hours
        result['Optimized_Hours'] = round(result['Calculated_Hours'] - potential_savings_hours, 2)
    else:
        result['Optimization_Potential_Hours'] = 0
        result['Optimized_Hours'] = result['Calculated_Hours']
    
    results.append(result)

df_results = pd.DataFrame(results)

print(f"✓ Analyzed {len(df_results)} documents")

# Calculate summary statistics
print("\n4. Calculating enhanced summary statistics...")

summary_stats = []
for category in categories:
    total_col = f'{category}_Total'
    unique_col = f'{category}_Unique'
    reusable_col = f'{category}_Reusable'
    
    if total_col in df_results.columns:
        total_sum = df_results[total_col].sum()
        unique_sum = df_results[unique_col].sum()
        reusable_sum = df_results[reusable_col].sum()
        
        # Count unique field codes
        unique_field_codes = len([
            field for field, cat in field_reusability.keys() 
            if cat == category and field_reusability[(field, cat)]['is_unique']
        ])
        
        total_field_codes = len(all_field_codes.get(category, set()))
        
        # Calculate average reusability score
        avg_reuse_score = np.mean([
            info['reusability_score'] 
            for (field, cat), info in field_reusability.items() 
            if cat == category
        ]) if total_field_codes > 0 else 0
        
        summary_stats.append({
            'Category': category,
            'Total_Instances': total_sum,
            'Unique_Instances': unique_sum,
            'Reusable_Instances': reusable_sum,
            'Unique_Ratio_%': round((unique_sum/total_sum*100), 1) if total_sum > 0 else 0,
            'Reusable_Ratio_%': round((reusable_sum/total_sum*100), 1) if total_sum > 0 else 0,
            'Unique_Patterns': unique_field_codes,
            'Total_Patterns': total_field_codes,
            'Avg_Reuse_Score': round(avg_reuse_score, 2),
            'Est_Hours': round(total_sum * effort_map.get(category, 10) / 60, 1),
            'Optimization_Potential_%': round((reusable_sum/total_sum*100 * 0.3), 1) if total_sum > 0 else 0
        })

df_summary = pd.DataFrame(summary_stats)

# Clean field codes for Excel
def clean_field_code(code):
    """Remove illegal characters for Excel"""
    if not code:
        return ""
    cleaned = ''.join(char if ord(char) >= 32 else ' ' for char in code)
    return cleaned[:250]  # Increased limit for better visibility

# Find most commonly reused fields
print("\n5. Identifying most commonly reused fields...")

reused_fields = []
for (field_code, category), info in field_reusability.items():
    if info['usage_count'] > 1:
        reused_fields.append({
            'Category': category,
            'Field_Sample': clean_field_code(field_code),
            'Usage_Count': info['usage_count'],
            'Documents_%': round((info['usage_count'] / 336) * 100, 1),
            'Reuse_Score': round(info['reusability_score'], 2),
            'Est_Savings_Hours': round((info['usage_count'] * effort_map.get(category, 10) * 0.3) / 60, 1)
        })

df_reused = pd.DataFrame(reused_fields)
if len(df_reused) > 0:
    df_reused = df_reused.sort_values('Usage_Count', ascending=False)

# Create pivot analysis
print("\n6. Creating pivot analysis...")

# Complexity distribution
complexity_dist = df_results['Complexity_Level'].value_counts().to_dict()

# Create document ranking
df_ranking = df_results[['ClientTitle', 'Total_All_Fields', 'Overall_Reusable_Ratio', 
                         'Calculated_Hours', 'Optimization_Potential_Hours', 
                         'Complexity_Level', 'Complexity_Score']].copy()
df_ranking = df_ranking.sort_values('Complexity_Score', ascending=False)

# Save everything to Excel
print("\n7. Saving enhanced results to Excel...")

output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/The336_Field_Analysis_Enhanced.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main analysis - all columns properly formatted
    df_results.to_excel(writer, sheet_name='336_Documents_Full', index=False)
    
    # Simplified view with key metrics only
    key_columns = ['ClientTitle', 'SQLFilename', 'Total_All_Fields', 
                   'Total_Unique_Fields', 'Total_Reusable_Fields',
                   'Overall_Unique_Ratio', 'Overall_Reusable_Ratio',
                   'Calculated_Hours', 'Optimization_Potential_Hours',
                   'Complexity_Level', 'Complexity_Score']
    df_results[key_columns].to_excel(writer, sheet_name='Key_Metrics', index=False)
    
    # Category summary
    df_summary.to_excel(writer, sheet_name='Category_Summary', index=False)
    
    # Top reused fields
    if len(df_reused) > 0:
        df_reused.head(100).to_excel(writer, sheet_name='Top_100_Reused_Fields', index=False)
    
    # Complexity ranking
    df_ranking.head(50).to_excel(writer, sheet_name='Complexity_Ranking', index=False)
    
    # Category breakdown per document (pivot table style)
    category_pivot = df_results[['ClientTitle'] + 
                                [f'{cat}_Total' for cat in categories]].copy()
    category_pivot.to_excel(writer, sheet_name='Fields_Per_Document', index=False)
    
    # Optimization summary
    optimization_summary = pd.DataFrame([{
        'Total_Documents': len(df_results),
        'Total_Fields': df_results['Total_All_Fields'].sum(),
        'Total_Unique_Fields': df_results['Total_Unique_Fields'].sum(),
        'Total_Reusable_Fields': df_results['Total_Reusable_Fields'].sum(),
        'Overall_Reusability_%': round((df_results['Total_Reusable_Fields'].sum() / 
                                       df_results['Total_All_Fields'].sum() * 100), 1),
        'Total_Est_Hours': round(df_results['Calculated_Hours'].sum(), 0),
        'Total_Optimization_Potential': round(df_results['Optimization_Potential_Hours'].sum(), 0),
        'Optimized_Total_Hours': round(df_results['Optimized_Hours'].sum(), 0),
        'Potential_Savings_%': round((df_results['Optimization_Potential_Hours'].sum() / 
                                     df_results['Calculated_Hours'].sum() * 100), 1)
    }])
    optimization_summary.to_excel(writer, sheet_name='Optimization_Summary', index=False)

print(f"✓ Saved to {output_file}")

# Print key findings
print("\n" + "=" * 80)
print("ENHANCED KEY FINDINGS")
print("=" * 80)

print("\n1. OVERALL STATISTICS:")
total_fields = df_results['Total_All_Fields'].sum()
unique_fields = df_results['Total_Unique_Fields'].sum()
reusable_fields = df_results['Total_Reusable_Fields'].sum()
print(f"   Total fields: {total_fields:,}")
print(f"   Unique fields: {unique_fields:,} ({unique_fields/total_fields*100:.1f}%)")
print(f"   Reusable fields: {reusable_fields:,} ({reusable_fields/total_fields*100:.1f}%)")

print("\n2. EFFORT ANALYSIS:")
total_hours = df_results['Calculated_Hours'].sum()
optimization_potential = df_results['Optimization_Potential_Hours'].sum()
optimized_hours = df_results['Optimized_Hours'].sum()
print(f"   Current estimate: {total_hours:.0f} hours")
print(f"   Optimization potential: {optimization_potential:.0f} hours")
print(f"   Optimized estimate: {optimized_hours:.0f} hours")
print(f"   Potential savings: {optimization_potential/total_hours*100:.1f}%")

print("\n3. COMPLEXITY DISTRIBUTION:")
for level in ['Very Low', 'Low', 'Medium', 'High', 'Very High']:
    count = len(df_results[df_results['Complexity_Level'] == level])
    if count > 0:
        print(f"   {level:10s}: {count:3d} documents ({count/336*100:.1f}%)")

print("\n4. TOP OPTIMIZATION OPPORTUNITIES:")
top_opt = df_results.nlargest(5, 'Optimization_Potential_Hours')[
    ['ClientTitle', 'Total_Reusable_Fields', 'Optimization_Potential_Hours']]
for idx, row in top_opt.iterrows():
    print(f"   {row['ClientTitle']:20s}: {row['Optimization_Potential_Hours']:.1f} hours potential savings")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE - Enhanced Excel file created with improved data quality")
print("=" * 80)
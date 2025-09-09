import json
import pandas as pd
from pathlib import Path
from collections import defaultdict
import numpy as np

print("=" * 80)
print("COMPLEXITY ANALYSIS WITH NEW RULES")
print("=" * 80)

# Load data
print("\n1. Loading data sources...")

# Load the 336 matched documents
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

print("\n2. Applying new complexity rules...")

"""
NEW COMPLEXITY RULES:
• Simple: under 10 fields AND no scripted fields and maximum 2 IF statements
• Moderate: between 10 and 20 fields (inclusive) AND fewer than 5 scripted fields and maximum of 20 IF statements
• Complex: everything else
"""

# Build field counts by document and category
fields_by_doc = defaultdict(lambda: defaultdict(list))

for record in field_analysis:
    doc_id = record['documentid']
    field_code = record.get('fieldcode', '') or ''
    category = record.get('field_category', 'Unknown')
    
    if field_code:
        fields_by_doc[doc_id][category].append(field_code)

print(f"✓ Processed fields for {len(fields_by_doc)} documents")

# Analyze each document with new rules
results = []
categories = ['If', 'Precedent Script', 'Reflection', 'Search', 'Unbound', 
              'Built In Script', 'Extended', 'Scripted']

# Define scripted field categories
scripted_categories = ['Precedent Script', 'Scripted', 'Built In Script']

for idx, row in matched_336.iterrows():
    doc_id = int(row['SQLDocID'])
    
    result = {
        'ClientTitle': row['ClientTitle'],
        'ClientDescription': row.get('ClientDescription', ''),
        'SQLDocID': doc_id,
        'SQLFilename': row['SQLFilename'],
        'OriginalComplexity': row.get('ClientComplexity', ''),
        'EstimatedHours': row.get('EstimatedHours', 0)
    }
    
    # Get document metadata
    if doc_id in doc_by_id:
        doc = doc_by_id[doc_id]
        result['Sections'] = doc.get('Sections', 0)
        result['Tables'] = doc.get('Tables', 0)
        result['Checkboxes'] = doc.get('Checkboxes', 0)
    
    # Count fields by category
    doc_fields = fields_by_doc.get(doc_id, {})
    
    # Calculate totals for complexity rules
    total_fields = sum(len(fields) for fields in doc_fields.values())
    if_statements = len(doc_fields.get('If', []))
    
    # Count scripted fields (Precedent Script, Scripted, Built In Script)
    scripted_fields = sum(len(doc_fields.get(cat, [])) for cat in scripted_categories)
    
    # Store field counts
    result['Total_Fields'] = total_fields
    result['IF_Statements'] = if_statements
    result['Scripted_Fields'] = scripted_fields
    
    # Add detailed breakdown
    for category in categories:
        result[f'{category}_Count'] = len(doc_fields.get(category, []))
    
    # Apply new complexity rules
    if total_fields < 10 and scripted_fields == 0 and if_statements <= 2:
        complexity = 'Simple'
        complexity_reason = f"<10 fields ({total_fields}), no scripts, ≤2 IFs ({if_statements})"
    elif 10 <= total_fields <= 20 and scripted_fields < 5 and if_statements <= 20:
        complexity = 'Moderate'
        complexity_reason = f"10-20 fields ({total_fields}), <5 scripts ({scripted_fields}), ≤20 IFs ({if_statements})"
    else:
        complexity = 'Complex'
        # Determine why it's complex
        reasons = []
        if total_fields > 20:
            reasons.append(f">20 fields ({total_fields})")
        if scripted_fields >= 5:
            reasons.append(f"≥5 scripts ({scripted_fields})")
        if if_statements > 20:
            reasons.append(f">20 IFs ({if_statements})")
        if total_fields >= 10 and (scripted_fields > 0 or if_statements > 2):
            if not reasons:  # Only add if no other reasons
                reasons.append(f"Moderate criteria exceeded")
        complexity_reason = "; ".join(reasons) if reasons else "Doesn't meet Simple/Moderate criteria"
    
    result['New_Complexity'] = complexity
    result['Complexity_Reason'] = complexity_reason
    
    # Calculate effort based on complexity
    if complexity == 'Simple':
        effort_multiplier = 1.0
    elif complexity == 'Moderate':
        effort_multiplier = 1.5
    else:  # Complex
        effort_multiplier = 2.5
    
    # Base effort calculation
    base_effort = total_fields * 0.5  # 30 minutes per field average
    adjusted_effort = base_effort * effort_multiplier
    result['Calculated_Hours'] = round(adjusted_effort, 2)
    
    # Comparison with original
    result['Hours_Difference'] = round(result['Calculated_Hours'] - result['EstimatedHours'], 2)
    
    results.append(result)

df_results = pd.DataFrame(results)

print(f"✓ Analyzed {len(df_results)} documents with new complexity rules")

# Calculate summary statistics
print("\n3. Calculating summary statistics...")

# Complexity distribution
complexity_counts = df_results['New_Complexity'].value_counts()
complexity_dist = complexity_counts.to_dict()

# Create summary by complexity
summary_by_complexity = []
for complexity in ['Simple', 'Moderate', 'Complex']:
    df_comp = df_results[df_results['New_Complexity'] == complexity]
    if len(df_comp) > 0:
        summary_by_complexity.append({
            'Complexity': complexity,
            'Count': len(df_comp),
            'Percentage': round(len(df_comp) / len(df_results) * 100, 1),
            'Avg_Total_Fields': round(df_comp['Total_Fields'].mean(), 1),
            'Avg_IF_Statements': round(df_comp['IF_Statements'].mean(), 1),
            'Avg_Scripted_Fields': round(df_comp['Scripted_Fields'].mean(), 1),
            'Min_Fields': df_comp['Total_Fields'].min(),
            'Max_Fields': df_comp['Total_Fields'].max(),
            'Total_Hours': round(df_comp['Calculated_Hours'].sum(), 0),
            'Avg_Hours': round(df_comp['Calculated_Hours'].mean(), 2)
        })

df_summary = pd.DataFrame(summary_by_complexity)

# Compare with original complexity
print("\n4. Comparing with original complexity classifications...")

comparison = pd.crosstab(
    df_results['OriginalComplexity'].fillna('Unknown'),
    df_results['New_Complexity'],
    margins=True,
    margins_name='Total'
)

# Find interesting cases
print("\n5. Identifying interesting cases...")

# Documents that changed complexity significantly
changed_complexity = df_results[
    (df_results['OriginalComplexity'].notna()) & 
    (df_results['OriginalComplexity'] != df_results['New_Complexity'])
].copy()

# Most complex documents
most_complex = df_results.nlargest(20, 'Total_Fields')[
    ['ClientTitle', 'Total_Fields', 'IF_Statements', 'Scripted_Fields', 
     'New_Complexity', 'Complexity_Reason', 'Calculated_Hours']
]

# Simple documents (optimization targets)
simple_docs = df_results[df_results['New_Complexity'] == 'Simple'][
    ['ClientTitle', 'Total_Fields', 'IF_Statements', 'Scripted_Fields', 
     'Calculated_Hours']
].sort_values('Total_Fields', ascending=False)

# Edge cases (just meeting/missing thresholds)
edge_cases = []
for idx, row in df_results.iterrows():
    # Near simple threshold
    if row['Total_Fields'] in [8, 9, 10, 11]:
        edge_cases.append({
            'ClientTitle': row['ClientTitle'],
            'Total_Fields': row['Total_Fields'],
            'IF_Statements': row['IF_Statements'],
            'Scripted_Fields': row['Scripted_Fields'],
            'Complexity': row['New_Complexity'],
            'Edge_Type': 'Near Simple/Moderate boundary'
        })
    # Near moderate threshold
    elif row['Total_Fields'] in [19, 20, 21]:
        edge_cases.append({
            'ClientTitle': row['ClientTitle'],
            'Total_Fields': row['Total_Fields'],
            'IF_Statements': row['IF_Statements'],
            'Scripted_Fields': row['Scripted_Fields'],
            'Complexity': row['New_Complexity'],
            'Edge_Type': 'Near Moderate/Complex boundary'
        })

df_edge_cases = pd.DataFrame(edge_cases)

# Save everything to Excel
print("\n6. Saving results to Excel...")

output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/Complexity_Analysis_New_Rules.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main results
    df_results.to_excel(writer, sheet_name='All_336_Documents', index=False)
    
    # Summary by complexity
    df_summary.to_excel(writer, sheet_name='Summary_By_Complexity', index=False)
    
    # Comparison with original
    comparison.to_excel(writer, sheet_name='Original_vs_New_Comparison')
    
    # Most complex documents
    most_complex.to_excel(writer, sheet_name='Top_20_Complex', index=False)
    
    # Simple documents
    if len(simple_docs) > 0:
        simple_docs.head(50).to_excel(writer, sheet_name='Simple_Documents', index=False)
    
    # Edge cases
    if len(df_edge_cases) > 0:
        df_edge_cases.to_excel(writer, sheet_name='Edge_Cases', index=False)
    
    # Changed complexity
    if len(changed_complexity) > 0:
        changed_complexity[['ClientTitle', 'OriginalComplexity', 'New_Complexity', 
                           'Total_Fields', 'IF_Statements', 'Scripted_Fields',
                           'Complexity_Reason']].to_excel(
            writer, sheet_name='Changed_Complexity', index=False)
    
    # Detailed field breakdown
    field_breakdown = df_results[['ClientTitle', 'Total_Fields'] + 
                                 [f'{cat}_Count' for cat in categories] + 
                                 ['New_Complexity']].copy()
    field_breakdown.to_excel(writer, sheet_name='Field_Breakdown', index=False)

print(f"✓ Saved to {output_file}")

# Create summary report
print("\n7. Creating summary report...")

report_content = f"""# Complexity Analysis Report - New Rules

**Date:** September 2025
**Documents Analyzed:** 336
**Analysis Based On:** SQL field_analysis.json

---

## New Complexity Rules Applied

### Simple
- **Criteria:** Under 10 fields AND no scripted fields AND maximum 2 IF statements
- **Count:** {complexity_dist.get('Simple', 0)} documents ({complexity_dist.get('Simple', 0)/336*100:.1f}%)
- **Total Effort:** {df_summary[df_summary['Complexity']=='Simple']['Total_Hours'].values[0] if 'Simple' in complexity_dist else 0:.0f} hours

### Moderate
- **Criteria:** 10-20 fields (inclusive) AND fewer than 5 scripted fields AND maximum 20 IF statements
- **Count:** {complexity_dist.get('Moderate', 0)} documents ({complexity_dist.get('Moderate', 0)/336*100:.1f}%)
- **Total Effort:** {df_summary[df_summary['Complexity']=='Moderate']['Total_Hours'].values[0] if 'Moderate' in complexity_dist else 0:.0f} hours

### Complex
- **Criteria:** Everything else (>20 fields OR ≥5 scripted fields OR >20 IF statements)
- **Count:** {complexity_dist.get('Complex', 0)} documents ({complexity_dist.get('Complex', 0)/336*100:.1f}%)
- **Total Effort:** {df_summary[df_summary['Complexity']=='Complex']['Total_Hours'].values[0] if 'Complex' in complexity_dist else 0:.0f} hours

---

## Key Statistics

### Overall Distribution
"""

for _, row in df_summary.iterrows():
    report_content += f"""
**{row['Complexity']}:**
- Documents: {row['Count']} ({row['Percentage']}%)
- Average Fields: {row['Avg_Total_Fields']}
- Average IF Statements: {row['Avg_IF_Statements']}
- Average Scripted Fields: {row['Avg_Scripted_Fields']}
- Field Range: {row['Min_Fields']}-{row['Max_Fields']}
- Total Hours: {row['Total_Hours']:.0f}
- Average Hours: {row['Avg_Hours']}
"""

report_content += f"""
---

## Total Project Effort

- **Total Estimated Hours:** {df_results['Calculated_Hours'].sum():.0f}
- **Average Hours per Document:** {df_results['Calculated_Hours'].mean():.2f}

---

## Migration Strategy Based on Complexity

### Phase 1: Simple Documents ({complexity_dist.get('Simple', 0)} documents)
- Can be largely automated
- Minimal scripting required
- Focus on templates and patterns
- Estimated effort: {df_summary[df_summary['Complexity']=='Simple']['Total_Hours'].values[0] if 'Simple' in complexity_dist else 0:.0f} hours

### Phase 2: Moderate Documents ({complexity_dist.get('Moderate', 0)} documents)
- Semi-automated approach
- Some custom scripting needed
- Reusable components applicable
- Estimated effort: {df_summary[df_summary['Complexity']=='Moderate']['Total_Hours'].values[0] if 'Moderate' in complexity_dist else 0:.0f} hours

### Phase 3: Complex Documents ({complexity_dist.get('Complex', 0)} documents)
- Requires manual review
- Significant custom development
- Individual testing needed
- Estimated effort: {df_summary[df_summary['Complexity']=='Complex']['Total_Hours'].values[0] if 'Complex' in complexity_dist else 0:.0f} hours

---

## Files Generated

1. **Complexity_Analysis_New_Rules.xlsx** - Complete analysis with 8 sheets
2. **Complexity_Report_New_Rules.md** - This summary report

---

*Analysis complete*
"""

report_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/Complexity_Report_New_Rules.md'
with open(report_file, 'w') as f:
    f.write(report_content)

print(f"✓ Saved report to {report_file}")

# Print console summary
print("\n" + "=" * 80)
print("COMPLEXITY ANALYSIS COMPLETE")
print("=" * 80)

print("\nCOMPLEXITY DISTRIBUTION (NEW RULES):")
for complexity in ['Simple', 'Moderate', 'Complex']:
    count = complexity_dist.get(complexity, 0)
    pct = count / 336 * 100
    print(f"  {complexity:10s}: {count:3d} documents ({pct:.1f}%)")

print("\nTOTAL EFFORT BY COMPLEXITY:")
for _, row in df_summary.iterrows():
    print(f"  {row['Complexity']:10s}: {row['Total_Hours']:6.0f} hours ({row['Total_Hours']/df_results['Calculated_Hours'].sum()*100:.1f}%)")

print(f"\nTOTAL PROJECT EFFORT: {df_results['Calculated_Hours'].sum():.0f} hours")

print("\nKEY INSIGHTS:")
print(f"  • {complexity_dist.get('Simple', 0)} documents can be largely automated")
print(f"  • {complexity_dist.get('Moderate', 0)} documents need semi-automated approach")
print(f"  • {complexity_dist.get('Complex', 0)} documents require individual attention")

# Find most complex
top_complex = df_results[df_results['New_Complexity'] == 'Complex'].nlargest(3, 'Total_Fields')
if len(top_complex) > 0:
    print("\nMOST COMPLEX DOCUMENTS:")
    for _, row in top_complex.iterrows():
        print(f"  • {row['ClientTitle']}: {row['Total_Fields']} fields, {row['Scripted_Fields']} scripts, {row['IF_Statements']} IFs")

print("\n" + "=" * 80)
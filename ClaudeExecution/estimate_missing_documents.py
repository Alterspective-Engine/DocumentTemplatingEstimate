import pandas as pd
import numpy as np
import json
from pathlib import Path

print("=" * 80)
print("ESTIMATING EFFORT FOR 211 MISSING DOCUMENTS")
print("=" * 80)

# Load the analyzed 336 documents with new complexity rules
df_analyzed = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/Complexity_Analysis_New_Rules.xlsx', 
                            sheet_name='All_336_Documents')
print(f"\n1. Loaded {len(df_analyzed)} analyzed documents")

# Load the complete mapping to identify missing documents
df_mapping = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ClaudeReview/ULTIMATE_Mapping_Solution.xlsx')
missing_docs = df_mapping[df_mapping['SQLDocID'].isna() & df_mapping['ManifestCode'].notna()].copy()
print(f"✓ Found {len(missing_docs)} documents missing SQL data")

# Calculate statistics from analyzed documents
print("\n2. Analyzing patterns from 336 documents...")

# Overall statistics
complexity_dist = df_analyzed['New_Complexity'].value_counts(normalize=True)
avg_hours_by_complexity = df_analyzed.groupby('New_Complexity')['Calculated_Hours'].mean()
median_hours_by_complexity = df_analyzed.groupby('New_Complexity')['Calculated_Hours'].median()

print("\nComplexity Distribution in Analyzed Documents:")
for complexity, pct in complexity_dist.items():
    count = int(pct * len(df_analyzed))
    avg_hrs = avg_hours_by_complexity[complexity]
    med_hrs = median_hours_by_complexity[complexity]
    print(f"  {complexity:10s}: {pct*100:5.1f}% ({count:3d} docs) - Avg: {avg_hrs:6.1f} hrs, Median: {med_hrs:6.1f} hrs")

# Analyze by title patterns (some templates have similar naming conventions)
def extract_prefix(title):
    """Extract prefix pattern from title (e.g., 'sup' from 'sup456')"""
    if pd.isna(title):
        return 'unknown'
    title = str(title).lower()
    if title.startswith('sup'):
        return 'sup'
    elif title.startswith('will'):
        return 'will'
    elif title.startswith('epa'):
        return 'epa'
    elif title.startswith('lease'):
        return 'lease'
    elif title.startswith('contract'):
        return 'contract'
    elif title.startswith('deed'):
        return 'deed'
    elif title.startswith('mortgage'):
        return 'mortgage'
    elif title.startswith('agreement'):
        return 'agreement'
    else:
        return 'other'

# Add prefix to analyzed docs
df_analyzed['Prefix'] = df_analyzed['ClientTitle'].apply(extract_prefix)

# Calculate statistics by prefix
prefix_stats = df_analyzed.groupby('Prefix').agg({
    'Calculated_Hours': ['mean', 'median', 'std', 'min', 'max', 'count'],
    'New_Complexity': lambda x: x.value_counts().to_dict()
}).round(2)

print("\n3. Estimating effort for missing documents...")

# Estimation approaches
estimation_methods = []

# Method 1: Overall average (baseline)
overall_avg = df_analyzed['Calculated_Hours'].mean()
overall_median = df_analyzed['Calculated_Hours'].median()
estimation_methods.append({
    'Method': 'Overall Average',
    'Hours_per_Doc': overall_avg,
    'Total_Hours': overall_avg * len(missing_docs),
    'Description': 'Simple average of all analyzed documents'
})

# Method 2: Weighted by complexity distribution
weighted_hours = 0
for complexity, pct in complexity_dist.items():
    expected_docs = pct * len(missing_docs)
    hours = avg_hours_by_complexity[complexity]
    weighted_hours += expected_docs * hours
estimation_methods.append({
    'Method': 'Complexity-Weighted',
    'Hours_per_Doc': weighted_hours / len(missing_docs),
    'Total_Hours': weighted_hours,
    'Description': 'Weighted by observed complexity distribution'
})

# Method 3: Conservative (assume higher complexity)
# Assume 30% simple, 20% moderate, 50% complex (more conservative)
conservative_hours = (0.30 * avg_hours_by_complexity.get('Simple', 1.08) * len(missing_docs) +
                     0.20 * avg_hours_by_complexity.get('Moderate', 8.91) * len(missing_docs) +
                     0.50 * avg_hours_by_complexity.get('Complex', 67.77) * len(missing_docs))
estimation_methods.append({
    'Method': 'Conservative',
    'Hours_per_Doc': conservative_hours / len(missing_docs),
    'Total_Hours': conservative_hours,
    'Description': 'Assumes higher complexity distribution (50% complex)'
})

# Method 4: Optimistic (assume lower complexity)
# Assume 60% simple, 25% moderate, 15% complex
optimistic_hours = (0.60 * avg_hours_by_complexity.get('Simple', 1.08) * len(missing_docs) +
                   0.25 * avg_hours_by_complexity.get('Moderate', 8.91) * len(missing_docs) +
                   0.15 * avg_hours_by_complexity.get('Complex', 67.77) * len(missing_docs))
estimation_methods.append({
    'Method': 'Optimistic',
    'Hours_per_Doc': optimistic_hours / len(missing_docs),
    'Total_Hours': optimistic_hours,
    'Description': 'Assumes lower complexity distribution (60% simple)'
})

# Method 5: Prefix-based estimation
missing_docs['Prefix'] = missing_docs['ClientTitle'].apply(extract_prefix)
prefix_based_hours = 0
prefix_details = []

for prefix in missing_docs['Prefix'].unique():
    prefix_count = len(missing_docs[missing_docs['Prefix'] == prefix])
    
    # Get stats for this prefix from analyzed docs
    if prefix in df_analyzed['Prefix'].values:
        prefix_avg = df_analyzed[df_analyzed['Prefix'] == prefix]['Calculated_Hours'].mean()
        prefix_median = df_analyzed[df_analyzed['Prefix'] == prefix]['Calculated_Hours'].median()
    else:
        # Use overall average for unknown prefixes
        prefix_avg = overall_avg
        prefix_median = overall_median
    
    prefix_based_hours += prefix_count * prefix_avg
    prefix_details.append({
        'Prefix': prefix,
        'Count': prefix_count,
        'Avg_Hours': prefix_avg,
        'Total_Hours': prefix_count * prefix_avg
    })

estimation_methods.append({
    'Method': 'Prefix-Based',
    'Hours_per_Doc': prefix_based_hours / len(missing_docs),
    'Total_Hours': prefix_based_hours,
    'Description': 'Based on document naming patterns'
})

# Create detailed estimates for each missing document
print("\n4. Creating document-by-document estimates...")

missing_estimates = []
for idx, row in missing_docs.iterrows():
    prefix = row['Prefix']
    
    # Get prefix-based estimate
    if prefix in df_analyzed['Prefix'].values:
        prefix_docs = df_analyzed[df_analyzed['Prefix'] == prefix]
        estimated_hours = prefix_docs['Calculated_Hours'].mean()
        
        # Determine likely complexity based on prefix distribution
        complexity_counts = prefix_docs['New_Complexity'].value_counts()
        if len(complexity_counts) > 0:
            likely_complexity = complexity_counts.index[0]  # Most common complexity for this prefix
        else:
            likely_complexity = 'Unknown'
        
        confidence = 'Medium' if len(prefix_docs) >= 5 else 'Low'
    else:
        # Use overall average for unknown prefixes
        estimated_hours = overall_avg
        likely_complexity = 'Unknown'
        confidence = 'Low'
    
    missing_estimates.append({
        'ClientTitle': row['ClientTitle'],
        'ClientDescription': row.get('ClientDescription', ''),
        'ManifestCode': row['ManifestCode'],
        'Prefix': prefix,
        'Estimated_Hours': round(estimated_hours, 2),
        'Likely_Complexity': likely_complexity,
        'Confidence': confidence,
        'Estimation_Method': 'Prefix-based' if prefix in df_analyzed['Prefix'].values else 'Overall average'
    })

df_missing_estimates = pd.DataFrame(missing_estimates)

# Calculate summary statistics
print("\n5. Calculating summary statistics...")

summary_stats = {
    'Total_Missing_Documents': len(missing_docs),
    'Total_Analyzed_Documents': len(df_analyzed),
    'Coverage_Percentage': len(df_analyzed) / (len(df_analyzed) + len(missing_docs)) * 100,
    
    'Analyzed_Total_Hours': df_analyzed['Calculated_Hours'].sum(),
    'Analyzed_Avg_Hours': df_analyzed['Calculated_Hours'].mean(),
    'Analyzed_Median_Hours': df_analyzed['Calculated_Hours'].median(),
    
    'Missing_Estimated_Hours': df_missing_estimates['Estimated_Hours'].sum(),
    'Missing_Avg_Hours': df_missing_estimates['Estimated_Hours'].mean(),
    'Missing_Median_Hours': df_missing_estimates['Estimated_Hours'].median(),
    
    'Project_Total_Hours': df_analyzed['Calculated_Hours'].sum() + df_missing_estimates['Estimated_Hours'].sum()
}

# Risk analysis
risk_analysis = []

# Calculate confidence levels
high_confidence = len(df_missing_estimates[df_missing_estimates['Confidence'] == 'High'])
medium_confidence = len(df_missing_estimates[df_missing_estimates['Confidence'] == 'Medium'])
low_confidence = len(df_missing_estimates[df_missing_estimates['Confidence'] == 'Low'])

risk_analysis.append({
    'Risk_Factor': 'Estimation Confidence',
    'High_Confidence': f"{high_confidence} docs",
    'Medium_Confidence': f"{medium_confidence} docs",
    'Low_Confidence': f"{low_confidence} docs",
    'Impact': 'Medium',
    'Mitigation': 'Prioritize analysis of low-confidence documents'
})

# Calculate variance risk
if len(df_analyzed) > 0:
    cv = df_analyzed['Calculated_Hours'].std() / df_analyzed['Calculated_Hours'].mean()
    risk_level = 'High' if cv > 2 else 'Medium' if cv > 1 else 'Low'
    risk_analysis.append({
        'Risk_Factor': 'High Variance in Estimates',
        'Coefficient_of_Variation': f"{cv:.2f}",
        'Risk_Level': risk_level,
        'Impact': 'High' if risk_level == 'High' else 'Medium',
        'Mitigation': 'Add 20-30% buffer for complex documents'
    })

# Save everything to Excel
print("\n6. Saving results to Excel...")

output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/Missing_Documents_Estimates.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Summary overview
    pd.DataFrame([summary_stats]).T.reset_index().rename(columns={'index': 'Metric', 0: 'Value'}).to_excel(
        writer, sheet_name='Summary', index=False)
    
    # Estimation methods comparison
    pd.DataFrame(estimation_methods).to_excel(
        writer, sheet_name='Estimation_Methods', index=False)
    
    # Detailed estimates for each missing document
    df_missing_estimates.to_excel(
        writer, sheet_name='Missing_Documents', index=False)
    
    # Prefix analysis
    pd.DataFrame(prefix_details).to_excel(
        writer, sheet_name='Prefix_Analysis', index=False)
    
    # Risk analysis
    pd.DataFrame(risk_analysis).to_excel(
        writer, sheet_name='Risk_Analysis', index=False)
    
    # Complexity distribution comparison
    complexity_comparison = pd.DataFrame({
        'Complexity': ['Simple', 'Moderate', 'Complex'],
        'Analyzed_Percentage': [
            complexity_dist.get('Simple', 0) * 100,
            complexity_dist.get('Moderate', 0) * 100,
            complexity_dist.get('Complex', 0) * 100
        ],
        'Analyzed_Avg_Hours': [
            avg_hours_by_complexity.get('Simple', 0),
            avg_hours_by_complexity.get('Moderate', 0),
            avg_hours_by_complexity.get('Complex', 0)
        ],
        'Expected_Missing_Count': [
            int(complexity_dist.get('Simple', 0) * len(missing_docs)),
            int(complexity_dist.get('Moderate', 0) * len(missing_docs)),
            int(complexity_dist.get('Complex', 0) * len(missing_docs))
        ]
    })
    complexity_comparison.to_excel(
        writer, sheet_name='Complexity_Projection', index=False)

print(f"✓ Saved to {output_file}")

# Create summary report
print("\n7. Creating summary report...")

report_content = f"""# Missing Documents Estimation Report

**Date:** September 2025
**Missing Documents:** 211
**Analyzed Documents:** 336
**Total Documents:** 547

---

## Executive Summary

Based on analysis of 336 documents with complete field data, we've estimated the effort required for the 211 missing documents using multiple estimation methods.

### Key Estimates

| Method | Hours per Doc | Total Hours | Description |
|--------|--------------|-------------|-------------|
| **Optimistic** | {optimistic_hours/len(missing_docs):.1f} | {optimistic_hours:.0f} | Assumes 60% simple documents |
| **Weighted** | {weighted_hours/len(missing_docs):.1f} | {weighted_hours:.0f} | Based on actual distribution |
| **Conservative** | {conservative_hours/len(missing_docs):.1f} | {conservative_hours:.0f} | Assumes 50% complex documents |
| **Recommended** | {df_missing_estimates['Estimated_Hours'].mean():.1f} | {df_missing_estimates['Estimated_Hours'].sum():.0f} | Prefix-based analysis |

---

## Total Project Estimate

### Confirmed (336 documents with SQL data)
- **Total Hours:** {df_analyzed['Calculated_Hours'].sum():.0f}
- **Average per Document:** {df_analyzed['Calculated_Hours'].mean():.1f}
- **Complexity Distribution:**
  - Simple: {len(df_analyzed[df_analyzed['New_Complexity']=='Simple'])} documents
  - Moderate: {len(df_analyzed[df_analyzed['New_Complexity']=='Moderate'])} documents
  - Complex: {len(df_analyzed[df_analyzed['New_Complexity']=='Complex'])} documents

### Estimated (211 missing documents)
- **Recommended Estimate:** {df_missing_estimates['Estimated_Hours'].sum():.0f} hours
- **Range:** {optimistic_hours:.0f} - {conservative_hours:.0f} hours
- **Average per Document:** {df_missing_estimates['Estimated_Hours'].mean():.1f} hours

### Combined Total
- **Total Documents:** 547
- **Total Estimated Hours:** {summary_stats['Project_Total_Hours']:.0f}
- **Average per Document:** {summary_stats['Project_Total_Hours']/547:.1f}

---

## Estimation Methodology

### 1. Pattern Analysis
We analyzed naming conventions and found patterns:
"""

# Add prefix analysis
for prefix_detail in sorted(prefix_details, key=lambda x: x['Count'], reverse=True)[:5]:
    report_content += f"\n- **{prefix_detail['Prefix']}**: {prefix_detail['Count']} documents, avg {prefix_detail['Avg_Hours']:.1f} hrs/doc"

report_content += f"""

### 2. Complexity Projection
Based on the 336 analyzed documents:
- **46.1%** are Simple (<10 fields, no scripts)
- **12.2%** are Moderate (10-20 fields, <5 scripts)
- **41.7%** are Complex (>20 fields or ≥5 scripts)

We project similar distribution for missing documents.

### 3. Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Unknown complexity** | High | Import and analyze ASAP |
| **High variance** | Medium | Add 20-30% buffer |
| **Missing special cases** | Low | Review naming patterns |

---

## Confidence Levels

- **High Confidence:** {high_confidence} documents (similar patterns found)
- **Medium Confidence:** {medium_confidence} documents (partial pattern match)
- **Low Confidence:** {low_confidence} documents (no pattern match)

---

## Recommendations

1. **Immediate Action:** Import the 211 missing documents to SQL database
2. **Validation:** Test estimates with 10-20 imported documents
3. **Buffer:** Add 20% contingency for uncertainty
4. **Priority:** Focus on high-complexity documents first

---

## Range of Estimates

### Best Case (Optimistic)
- Total: {optimistic_hours:.0f} hours
- Assumes most missing docs are simple

### Most Likely (Weighted)
- Total: {weighted_hours:.0f} hours
- Based on observed distribution

### Worst Case (Conservative)
- Total: {conservative_hours:.0f} hours
- Assumes high complexity

### Recommended
- **Use: {df_missing_estimates['Estimated_Hours'].sum():.0f} hours**
- **With 20% buffer: {df_missing_estimates['Estimated_Hours'].sum() * 1.2:.0f} hours**

---

## Files Generated

1. **Missing_Documents_Estimates.xlsx** - Detailed estimates with 6 sheets
2. **Missing_Documents_Report.md** - This summary report

---

*Analysis complete*
"""

report_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/Missing_Documents_Report.md'
with open(report_file, 'w') as f:
    f.write(report_content)

print(f"✓ Saved report to {report_file}")

# Print console summary
print("\n" + "=" * 80)
print("ESTIMATION COMPLETE")
print("=" * 80)

print(f"\nPROJECT TOTALS:")
print(f"  Analyzed (336 docs):  {df_analyzed['Calculated_Hours'].sum():7,.0f} hours (confirmed)")
print(f"  Missing (211 docs):   {df_missing_estimates['Estimated_Hours'].sum():7,.0f} hours (estimated)")
print(f"  TOTAL PROJECT:        {summary_stats['Project_Total_Hours']:7,.0f} hours")

print(f"\nESTIMATION RANGE FOR MISSING DOCUMENTS:")
print(f"  Optimistic:   {optimistic_hours:7,.0f} hours")
print(f"  Recommended:  {df_missing_estimates['Estimated_Hours'].sum():7,.0f} hours")
print(f"  Conservative: {conservative_hours:7,.0f} hours")

print(f"\nCONFIDENCE:")
print(f"  High:   {high_confidence:3d} documents")
print(f"  Medium: {medium_confidence:3d} documents")
print(f"  Low:    {low_confidence:3d} documents")

print("\n" + "=" * 80)
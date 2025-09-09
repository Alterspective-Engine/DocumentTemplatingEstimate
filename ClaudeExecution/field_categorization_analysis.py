import json
from pathlib import Path
from collections import defaultdict, Counter
import pandas as pd

print("=" * 80)
print("FIELD CATEGORIZATION AND SCRIPT COMPLEXITY ANALYSIS")
print("=" * 80)

# Load the data
print("\n1. Loading data files...")
newSQL_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL')

# Load field analysis
with open(newSQL_path / 'field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ Loaded {len(field_analysis)} field analyses")

# Load documents
with open(newSQL_path / 'documents.json', 'r') as f:
    documents = json.load(f)
print(f"✓ Loaded {len(documents)} documents")

# Build document profiles
print("\n2. Building document field profiles...")
doc_field_profiles = defaultdict(lambda: defaultdict(int))
doc_field_details = defaultdict(list)

for record in field_analysis:
    doc_id = record['documentid']
    category = record['field_category']
    field_code = record.get('fieldcode', '')
    
    doc_field_profiles[doc_id][category] += 1
    doc_field_details[doc_id].append({
        'category': category,
        'fieldcode': field_code
    })

print(f"✓ Built profiles for {len(doc_field_profiles)} documents")

# Create document lookup
doc_lookup = {doc['DocumentID']: doc for doc in documents}

def calculate_script_complexity(doc):
    """Calculate script complexity based on document metadata"""
    complexity = 0
    
    # Check for SEQ fields (sequential numbering/logic)
    seq_fields = doc.get('SEQFields', 0)
    if seq_fields > 0:
        complexity += min(seq_fields * 2, 20)  # Cap at 20 points
    
    # Check for REF fields (references/cross-references)
    ref_fields = doc.get('REFFields', 0)
    if ref_fields > 0:
        complexity += min(ref_fields * 1, 10)  # Cap at 10 points
    
    # Check for checkboxes (form logic)
    checkboxes = doc.get('Checkboxes', 0)
    if checkboxes > 0:
        complexity += min(checkboxes * 0.5, 5)  # Cap at 5 points
    
    # Check for TOC (complex document structure)
    toc = doc.get('TOC', 0)
    if toc > 0:
        complexity += 5
    
    # Check for compatibility mode (potential legacy issues)
    compat_mode = doc.get('CompatibilityMode', 0)
    if compat_mode == 1:
        complexity += 10  # Compatibility mode adds complexity
    
    # Check for high section count (document complexity)
    sections = doc.get('Sections', 0)
    if sections > 10:
        complexity += min((sections - 10) * 0.5, 10)
    
    # Check for tables (structured data)
    tables = doc.get('Tables', 0)
    if tables > 0:
        complexity += min(tables * 2, 15)
    
    return int(complexity)

def generate_reasoning(doc, field_profile):
    """Generate reasoning for field categorization"""
    reasoning_parts = []
    
    # Analyze field categories
    if field_profile:
        total_fields = sum(field_profile.values())
        dominant_category = max(field_profile.items(), key=lambda x: x[1])[0] if field_profile else None
        
        if dominant_category:
            dominant_count = field_profile[dominant_category]
            dominant_pct = (dominant_count / total_fields * 100) if total_fields > 0 else 0
            reasoning_parts.append(f"Document has {total_fields} fields with {dominant_category} being dominant ({dominant_count} instances, {dominant_pct:.1f}%)")
        
        # List all categories
        category_summary = []
        for cat, count in sorted(field_profile.items(), key=lambda x: x[1], reverse=True):
            category_summary.append(f"{cat}: {count}")
        reasoning_parts.append(f"Field distribution: {', '.join(category_summary)}")
    else:
        reasoning_parts.append("No field analysis data available")
    
    # Analyze document structure
    structure_info = []
    if doc.get('Sections', 0) > 0:
        structure_info.append(f"{doc['Sections']} sections")
    if doc.get('Tables', 0) > 0:
        structure_info.append(f"{doc['Tables']} tables")
    if doc.get('SEQFields', 0) > 0:
        structure_info.append(f"{doc['SEQFields']} SEQ fields")
    if doc.get('REFFields', 0) > 0:
        structure_info.append(f"{doc['REFFields']} REF fields")
    if doc.get('Checkboxes', 0) > 0:
        structure_info.append(f"{doc['Checkboxes']} checkboxes")
    if doc.get('TOC', 0) > 0:
        structure_info.append("TOC present")
    if doc.get('CompatibilityMode', 0) == 1:
        structure_info.append("compatibility mode enabled")
    
    if structure_info:
        reasoning_parts.append(f"Document structure: {', '.join(structure_info)}")
    
    return ". ".join(reasoning_parts)

def generate_conclusion(field_profile, script_complexity):
    """Generate conclusion based on analysis"""
    conclusions = []
    
    # Assess overall complexity
    if script_complexity == 0:
        complexity_level = "No scripting"
    elif script_complexity < 10:
        complexity_level = "Low complexity"
    elif script_complexity < 25:
        complexity_level = "Moderate complexity"
    elif script_complexity < 50:
        complexity_level = "High complexity"
    else:
        complexity_level = "Very high complexity"
    
    conclusions.append(f"{complexity_level} (score: {script_complexity})")
    
    # Assess field requirements
    if field_profile:
        total_fields = sum(field_profile.values())
        
        # Check for complex field types
        complex_fields = 0
        if 'Precedent Script' in field_profile:
            complex_fields += field_profile['Precedent Script']
        if 'Scripted' in field_profile:
            complex_fields += field_profile['Scripted']
        if 'Built In Script' in field_profile:
            complex_fields += field_profile['Built In Script']
        
        if complex_fields > 0:
            conclusions.append(f"{complex_fields} complex script fields require careful analysis")
        
        # Check for conditional logic
        if 'If' in field_profile or 'If Statement' in field_profile:
            if_count = field_profile.get('If', 0) + field_profile.get('If Statement', 0)
            conclusions.append(f"{if_count} conditional statements need implementation")
        
        # Estimate effort
        effort_hours = estimate_effort(field_profile, script_complexity)
        conclusions.append(f"Estimated effort: {effort_hours:.1f} hours")
    
    return ". ".join(conclusions)

def estimate_effort(field_profile, script_complexity):
    """Estimate effort in hours based on field profile and complexity"""
    effort_minutes = 0
    
    # Field-based effort (from BecInfo.txt)
    field_effort = {
        'Reflection': 5,
        'Extended': 5,
        'Unbound': 5,  # Plus 15 for form creation
        'Search': 10,
        'If': 15,
        'If Statement': 15,
        'Built In Script': 20,
        'Scripted': 30,
        'Precedent Script': 30
    }
    
    for category, count in field_profile.items():
        minutes_per = field_effort.get(category, 10)  # Default 10 minutes
        effort_minutes += count * minutes_per
    
    # Add form creation time for unbound fields
    if field_profile.get('Unbound', 0) > 0:
        effort_minutes += 15
    
    # Add complexity factor
    if script_complexity > 25:
        effort_minutes *= 1.5  # 50% more time for high complexity
    elif script_complexity > 50:
        effort_minutes *= 2.0  # Double time for very high complexity
    
    return effort_minutes / 60

# Analyze all documents
print("\n3. Analyzing all documents...")
analysis_results = []

for doc_id, doc in doc_lookup.items():
    field_profile = doc_field_profiles.get(doc_id, {})
    
    # Determine primary field category
    if field_profile:
        primary_category = max(field_profile.items(), key=lambda x: x[1])[0]
    else:
        primary_category = "No field data"
    
    # Calculate script complexity
    script_complexity = calculate_script_complexity(doc)
    
    # Generate reasoning
    reasoning = generate_reasoning(doc, field_profile)
    
    # Generate conclusion
    conclusion = generate_conclusion(field_profile, script_complexity)
    
    result = {
        "document_id": doc_id,
        "filename": doc.get('Filename', 'Unknown'),
        "field_category": primary_category,
        "reasoning": reasoning,
        "script_complexity": script_complexity,
        "conclusion": conclusion
    }
    
    analysis_results.append(result)

# Sort by script complexity (highest first)
analysis_results.sort(key=lambda x: x['script_complexity'], reverse=True)

# Save results
print("\n4. Saving analysis results...")

# Save full JSON output
output_file = Path('../ClaudeReview/field_categorization_analysis.json')
with open(output_file, 'w') as f:
    json.dump(analysis_results, f, indent=2)
print(f"✓ Saved full analysis to {output_file}")

# Create summary statistics
print("\n5. Generating summary statistics...")

# Field category distribution
category_counter = Counter(r['field_category'] for r in analysis_results)
print("\nPrimary Field Category Distribution:")
for category, count in category_counter.most_common():
    pct = count / len(analysis_results) * 100
    print(f"  {category:20s}: {count:4d} ({pct:.1f}%)")

# Script complexity distribution
complexity_ranges = {
    'No scripting (0)': 0,
    'Low (1-9)': 0,
    'Moderate (10-24)': 0,
    'High (25-49)': 0,
    'Very High (50+)': 0
}

for result in analysis_results:
    score = result['script_complexity']
    if score == 0:
        complexity_ranges['No scripting (0)'] += 1
    elif score < 10:
        complexity_ranges['Low (1-9)'] += 1
    elif score < 25:
        complexity_ranges['Moderate (10-24)'] += 1
    elif score < 50:
        complexity_ranges['High (25-49)'] += 1
    else:
        complexity_ranges['Very High (50+)'] += 1

print("\nScript Complexity Distribution:")
for range_name, count in complexity_ranges.items():
    pct = count / len(analysis_results) * 100
    print(f"  {range_name:20s}: {count:4d} ({pct:.1f}%)")

# Top 10 most complex documents
print("\nTop 10 Most Complex Documents:")
for i, result in enumerate(analysis_results[:10], 1):
    print(f"  {i:2d}. {result['filename']:30s} - Complexity: {result['script_complexity']:3d} - Category: {result['field_category']}")

# Create Excel report
print("\n6. Creating Excel report...")
df_results = pd.DataFrame(analysis_results)

# Add additional calculated columns
df_results['has_scripts'] = df_results['script_complexity'] > 0
df_results['complexity_level'] = df_results['script_complexity'].apply(lambda x: 
    'No scripting' if x == 0 else
    'Low' if x < 10 else
    'Moderate' if x < 25 else
    'High' if x < 50 else
    'Very High'
)

excel_file = Path('../ClaudeReview/field_categorization_analysis.xlsx')
with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
    # Full results
    df_results.to_excel(writer, sheet_name='Full Analysis', index=False)
    
    # Summary statistics
    summary_stats = pd.DataFrame({
        'Metric': [
            'Total Documents',
            'Documents with Field Data',
            'Documents with Scripts',
            'Average Script Complexity',
            'Max Script Complexity'
        ],
        'Value': [
            len(df_results),
            len([r for r in analysis_results if r['field_category'] != 'No field data']),
            len(df_results[df_results['has_scripts']]),
            f"{df_results['script_complexity'].mean():.2f}",
            df_results['script_complexity'].max()
        ]
    })
    summary_stats.to_excel(writer, sheet_name='Summary', index=False)
    
    # Category distribution
    category_df = pd.DataFrame(category_counter.items(), columns=['Category', 'Count'])
    category_df['Percentage'] = (category_df['Count'] / len(analysis_results) * 100).round(1)
    category_df.sort_values('Count', ascending=False, inplace=True)
    category_df.to_excel(writer, sheet_name='Category Distribution', index=False)
    
    # Complexity distribution
    complexity_df = pd.DataFrame(complexity_ranges.items(), columns=['Complexity Range', 'Count'])
    complexity_df['Percentage'] = (complexity_df['Count'] / len(analysis_results) * 100).round(1)
    complexity_df.to_excel(writer, sheet_name='Complexity Distribution', index=False)

print(f"✓ Saved Excel report to {excel_file}")

# Print sample output in requested format
print("\n" + "=" * 80)
print("SAMPLE OUTPUT (First 3 documents)")
print("=" * 80)

for result in analysis_results[:3]:
    print(f"\nDocument: {result['filename']}")
    print(json.dumps({
        "field_category": result['field_category'],
        "reasoning": result['reasoning'],
        "script_complexity": result['script_complexity'],
        "conclusion": result['conclusion']
    }, indent=2))

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
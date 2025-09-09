import pandas as pd
import numpy as np
import json
from collections import defaultdict

print("=" * 80)
print("CREATING CLEAR FIELD ANALYSIS WITH COMPREHENSIVE KEY")
print("=" * 80)

# Load data sources
print("\n1. Loading data sources...")

# Load the mapping
df_mapping = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ClaudeReview/ULTIMATE_Mapping_Solution.xlsx')
matched_336 = df_mapping[df_mapping['SQLDocID'].notna()].copy()
print(f"✓ Found {len(matched_336)} documents with SQL data")

# Load field analysis
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/field_analysis.json', 'r') as f:
    field_analysis = json.load(f)

# Load documents for metadata
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    sql_documents = json.load(f)
doc_by_id = {d['DocumentID']: d for d in sql_documents}

print("\n2. Processing field data with clear categorization...")

# Build comprehensive field data
fields_by_doc = defaultdict(lambda: defaultdict(list))
field_occurrence = defaultdict(lambda: defaultdict(set))

for record in field_analysis:
    doc_id = record['documentid']
    field_code = record.get('fieldcode', '') or ''
    field_code = field_code.strip() if field_code else ''
    category = record.get('field_category', 'Unknown')
    
    if field_code:
        fields_by_doc[doc_id][category].append(field_code)
        field_occurrence[field_code][category].add(doc_id)

# Analyze reusability
field_reusability = {}
for field_code, categories in field_occurrence.items():
    for category, doc_ids in categories.items():
        usage_count = len(doc_ids)
        field_reusability[(field_code, category)] = {
            'usage_count': usage_count,
            'is_unique': usage_count == 1,
            'is_reusable': usage_count > 1
        }

print("\n3. Building comprehensive document analysis...")

# Define field categories clearly
categories = ['If', 'Precedent Script', 'Reflection', 'Search', 'Unbound', 
              'Built In Script', 'Extended', 'Scripted']

# Scripted categories for complexity rules
scripted_categories = ['Precedent Script', 'Scripted', 'Built In Script']

results = []
for idx, row in matched_336.iterrows():
    doc_id = int(row['SQLDocID'])
    
    # Basic document info
    result = {
        'Document_Name': row['ClientTitle'],
        'SQL_Document_ID': doc_id,
        'SQL_Filename': row['SQLFilename'],
        'Client_Description': row.get('ClientDescription', ''),
        'Original_Hours_Estimate': row.get('EstimatedHours', 0)
    }
    
    # Get document metadata
    if doc_id in doc_by_id:
        doc = doc_by_id[doc_id]
        result['Document_Sections'] = doc.get('Sections', 0)
        result['Document_Tables'] = doc.get('Tables', 0)
        result['Document_Checkboxes'] = doc.get('Checkboxes', 0)
    else:
        result['Document_Sections'] = 0
        result['Document_Tables'] = 0
        result['Document_Checkboxes'] = 0
    
    # Get fields for this document
    doc_fields = fields_by_doc.get(doc_id, {})
    
    # Count fields by category with clear naming
    total_all_fields = 0
    
    # IF Statements
    if_fields = doc_fields.get('If', [])
    result['IF_Statement_Count'] = len(if_fields)
    total_all_fields += len(if_fields)
    
    # Count unique vs reusable IF statements
    if_unique = sum(1 for f in if_fields if field_reusability.get((f, 'If'), {}).get('is_unique', False))
    if_reusable = len(if_fields) - if_unique
    result['IF_Unique_Count'] = if_unique
    result['IF_Reusable_Count'] = if_reusable
    result['IF_Reuse_Rate'] = f"{(if_reusable/len(if_fields)*100):.1f}%" if len(if_fields) > 0 else "0.0%"
    
    # Precedent Scripts
    prec_fields = doc_fields.get('Precedent Script', [])
    result['Precedent_Script_Count'] = len(prec_fields)
    total_all_fields += len(prec_fields)
    
    prec_unique = sum(1 for f in prec_fields if field_reusability.get((f, 'Precedent Script'), {}).get('is_unique', False))
    prec_reusable = len(prec_fields) - prec_unique
    result['Precedent_Unique_Count'] = prec_unique
    result['Precedent_Reusable_Count'] = prec_reusable
    result['Precedent_Reuse_Rate'] = f"{(prec_reusable/len(prec_fields)*100):.1f}%" if len(prec_fields) > 0 else "0.0%"
    
    # Reflection Fields
    refl_fields = doc_fields.get('Reflection', [])
    result['Reflection_Field_Count'] = len(refl_fields)
    total_all_fields += len(refl_fields)
    
    refl_unique = sum(1 for f in refl_fields if field_reusability.get((f, 'Reflection'), {}).get('is_unique', False))
    refl_reusable = len(refl_fields) - refl_unique
    result['Reflection_Unique_Count'] = refl_unique
    result['Reflection_Reusable_Count'] = refl_reusable
    result['Reflection_Reuse_Rate'] = f"{(refl_reusable/len(refl_fields)*100):.1f}%" if len(refl_fields) > 0 else "0.0%"
    
    # Search Fields
    search_fields = doc_fields.get('Search', [])
    result['Search_Field_Count'] = len(search_fields)
    total_all_fields += len(search_fields)
    
    search_unique = sum(1 for f in search_fields if field_reusability.get((f, 'Search'), {}).get('is_unique', False))
    search_reusable = len(search_fields) - search_unique
    result['Search_Unique_Count'] = search_unique
    result['Search_Reusable_Count'] = search_reusable
    result['Search_Reuse_Rate'] = f"{(search_reusable/len(search_fields)*100):.1f}%" if len(search_fields) > 0 else "0.0%"
    
    # Unbound Fields
    unbound_fields = doc_fields.get('Unbound', [])
    result['Unbound_Field_Count'] = len(unbound_fields)
    total_all_fields += len(unbound_fields)
    
    unbound_unique = sum(1 for f in unbound_fields if field_reusability.get((f, 'Unbound'), {}).get('is_unique', False))
    unbound_reusable = len(unbound_fields) - unbound_unique
    result['Unbound_Unique_Count'] = unbound_unique
    result['Unbound_Reusable_Count'] = unbound_reusable
    result['Unbound_Reuse_Rate'] = f"{(unbound_reusable/len(unbound_fields)*100):.1f}%" if len(unbound_fields) > 0 else "0.0%"
    
    # Built-In Scripts
    builtin_fields = doc_fields.get('Built In Script', [])
    result['BuiltIn_Script_Count'] = len(builtin_fields)
    total_all_fields += len(builtin_fields)
    
    builtin_unique = sum(1 for f in builtin_fields if field_reusability.get((f, 'Built In Script'), {}).get('is_unique', False))
    builtin_reusable = len(builtin_fields) - builtin_unique
    result['BuiltIn_Unique_Count'] = builtin_unique
    result['BuiltIn_Reusable_Count'] = builtin_reusable
    result['BuiltIn_Reuse_Rate'] = f"{(builtin_reusable/len(builtin_fields)*100):.1f}%" if len(builtin_fields) > 0 else "0.0%"
    
    # Extended Fields
    extended_fields = doc_fields.get('Extended', [])
    result['Extended_Field_Count'] = len(extended_fields)
    total_all_fields += len(extended_fields)
    
    extended_unique = sum(1 for f in extended_fields if field_reusability.get((f, 'Extended'), {}).get('is_unique', False))
    extended_reusable = len(extended_fields) - extended_unique
    result['Extended_Unique_Count'] = extended_unique
    result['Extended_Reusable_Count'] = extended_reusable
    result['Extended_Reuse_Rate'] = f"{(extended_reusable/len(extended_fields)*100):.1f}%" if len(extended_fields) > 0 else "0.0%"
    
    # Scripted Fields
    scripted_fields = doc_fields.get('Scripted', [])
    result['Scripted_Field_Count'] = len(scripted_fields)
    total_all_fields += len(scripted_fields)
    
    scripted_unique = sum(1 for f in scripted_fields if field_reusability.get((f, 'Scripted'), {}).get('is_unique', False))
    scripted_reusable = len(scripted_fields) - scripted_unique
    result['Scripted_Unique_Count'] = scripted_unique
    result['Scripted_Reusable_Count'] = scripted_reusable
    result['Scripted_Reuse_Rate'] = f"{(scripted_reusable/len(scripted_fields)*100):.1f}%" if len(scripted_fields) > 0 else "0.0%"
    
    # TOTALS
    result['TOTAL_All_Fields'] = total_all_fields
    
    # Calculate total unique fields
    total_unique = (if_unique + prec_unique + refl_unique + search_unique + 
                   unbound_unique + builtin_unique + extended_unique + scripted_unique)
    result['TOTAL_Unique_Fields'] = total_unique
    result['TOTAL_Reusable_Fields'] = total_all_fields - total_unique
    result['TOTAL_Reuse_Rate'] = f"{((total_all_fields - total_unique)/total_all_fields*100):.1f}%" if total_all_fields > 0 else "0.0%"
    
    # COMPLEXITY CALCULATION (New Rules)
    total_scripted = len(prec_fields) + len(scripted_fields) + len(builtin_fields)
    
    if total_all_fields < 10 and total_scripted == 0 and len(if_fields) <= 2:
        complexity = 'Simple'
        complexity_reason = f"<10 fields ({total_all_fields}), no scripts, ≤2 IFs ({len(if_fields)})"
    elif 10 <= total_all_fields <= 20 and total_scripted < 5 and len(if_fields) <= 20:
        complexity = 'Moderate'
        complexity_reason = f"10-20 fields ({total_all_fields}), <5 scripts ({total_scripted}), ≤20 IFs ({len(if_fields)})"
    else:
        complexity = 'Complex'
        reasons = []
        if total_all_fields > 20:
            reasons.append(f">20 fields ({total_all_fields})")
        if total_scripted >= 5:
            reasons.append(f"≥5 scripts ({total_scripted})")
        if len(if_fields) > 20:
            reasons.append(f">20 IFs ({len(if_fields)})")
        complexity_reason = "; ".join(reasons) if reasons else "Doesn't meet Simple/Moderate criteria"
    
    result['Complexity_Level'] = complexity
    result['Complexity_Reason'] = complexity_reason
    
    # EFFORT CALCULATION
    # Base effort: 30 minutes (0.5 hours) per field
    base_effort = total_all_fields * 0.5
    
    # Apply complexity multiplier
    if complexity == 'Simple':
        multiplier = 1.0
    elif complexity == 'Moderate':
        multiplier = 1.5
    else:  # Complex
        multiplier = 2.5
    
    calculated_hours = base_effort * multiplier
    result['Calculated_Hours'] = round(calculated_hours, 2)
    
    # Optimization potential
    if result['TOTAL_Reuse_Rate'] != "0.0%":
        reuse_pct = float(result['TOTAL_Reuse_Rate'].replace('%', '')) / 100
        potential_savings = calculated_hours * reuse_pct * 0.4  # 40% savings on reusable fields
        result['Potential_Savings_Hours'] = round(potential_savings, 2)
        result['Optimized_Hours'] = round(calculated_hours - potential_savings, 2)
    else:
        result['Potential_Savings_Hours'] = 0
        result['Optimized_Hours'] = result['Calculated_Hours']
    
    results.append(result)

df_results = pd.DataFrame(results)

print("\n4. Creating field definitions key...")

# Create comprehensive key/legend
field_definitions = [
    {
        'Field_Name': 'Document_Name',
        'Description': 'Client template name (e.g., sup456)',
        'Source': 'ClientRequirements.xlsx - ClientTitle column',
        'Data_Type': 'Text'
    },
    {
        'Field_Name': 'SQL_Document_ID',
        'Description': 'Unique identifier in SQL database',
        'Source': 'SQL Database - DocumentID',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'SQL_Filename',
        'Description': 'Filename in SQL database (e.g., 2694.dot)',
        'Source': 'SQL Database - Filename',
        'Data_Type': 'Text'
    },
    {
        'Field_Name': 'Client_Description',
        'Description': 'Description of template purpose',
        'Source': 'ClientRequirements.xlsx - ClientDescription column',
        'Data_Type': 'Text'
    },
    {
        'Field_Name': 'Original_Hours_Estimate',
        'Description': 'Original effort estimate from client',
        'Source': 'ClientRequirements.xlsx - EstimatedHours column',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Document_Sections',
        'Description': 'Number of document sections',
        'Source': 'SQL documents.json - Sections field',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Document_Tables',
        'Description': 'Number of tables in document',
        'Source': 'SQL documents.json - Tables field',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Document_Checkboxes',
        'Description': 'Number of checkboxes in document',
        'Source': 'SQL documents.json - Checkboxes field',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'IF_Statement_Count',
        'Description': 'Number of conditional logic fields (IF/THEN statements)',
        'Source': 'SQL field_analysis.json - field_category="If"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'IF_Unique_Count',
        'Description': 'IF statements unique to this document only',
        'Source': 'Calculated: IF fields appearing in only 1 document',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'IF_Reusable_Count',
        'Description': 'IF statements used in multiple documents',
        'Source': 'Calculated: IF fields appearing in >1 document',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'IF_Reuse_Rate',
        'Description': 'Percentage of IF statements that are reusable',
        'Source': 'Calculated: (IF_Reusable_Count / IF_Statement_Count) * 100',
        'Data_Type': 'Percentage'
    },
    {
        'Field_Name': 'Precedent_Script_Count',
        'Description': 'Custom C# scripts specific to this precedent',
        'Source': 'SQL field_analysis.json - field_category="Precedent Script"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Precedent_Unique_Count',
        'Description': 'Precedent scripts unique to this document',
        'Source': 'Calculated: Precedent Script fields in only 1 document',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Precedent_Reusable_Count',
        'Description': 'Precedent scripts used in multiple documents',
        'Source': 'Calculated: Precedent Script fields in >1 document',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Precedent_Reuse_Rate',
        'Description': 'Percentage of precedent scripts that are reusable',
        'Source': 'Calculated: (Precedent_Reusable_Count / Precedent_Script_Count) * 100',
        'Data_Type': 'Percentage'
    },
    {
        'Field_Name': 'Reflection_Field_Count',
        'Description': 'Fields that reference/display data from other fields',
        'Source': 'SQL field_analysis.json - field_category="Reflection"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Search_Field_Count',
        'Description': 'Database lookup/search fields',
        'Source': 'SQL field_analysis.json - field_category="Search"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Unbound_Field_Count',
        'Description': 'Fields not bound to database columns (temporary/calculated)',
        'Source': 'SQL field_analysis.json - field_category="Unbound"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'BuiltIn_Script_Count',
        'Description': 'Standard reusable scripts from system library',
        'Source': 'SQL field_analysis.json - field_category="Built In Script"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Extended_Field_Count',
        'Description': 'Extended/custom field types with additional properties',
        'Source': 'SQL field_analysis.json - field_category="Extended"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Scripted_Field_Count',
        'Description': 'General scripted fields with custom code',
        'Source': 'SQL field_analysis.json - field_category="Scripted"',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'TOTAL_All_Fields',
        'Description': 'Sum of all field types in document',
        'Source': 'Calculated: Sum of all *_Count fields',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'TOTAL_Unique_Fields',
        'Description': 'Total fields unique to this document',
        'Source': 'Calculated: Sum of all *_Unique_Count fields',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'TOTAL_Reusable_Fields',
        'Description': 'Total fields that appear in multiple documents',
        'Source': 'Calculated: TOTAL_All_Fields - TOTAL_Unique_Fields',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'TOTAL_Reuse_Rate',
        'Description': 'Overall percentage of fields that are reusable',
        'Source': 'Calculated: (TOTAL_Reusable_Fields / TOTAL_All_Fields) * 100',
        'Data_Type': 'Percentage'
    },
    {
        'Field_Name': 'Complexity_Level',
        'Description': 'Simple/Moderate/Complex based on new rules',
        'Source': 'Calculated: Rules - Simple (<10 fields, 0 scripts, ≤2 IFs), Moderate (10-20 fields, <5 scripts, ≤20 IFs), Complex (everything else)',
        'Data_Type': 'Category'
    },
    {
        'Field_Name': 'Complexity_Reason',
        'Description': 'Explanation of why document received its complexity rating',
        'Source': 'Calculated: Based on which complexity rule thresholds were met/exceeded',
        'Data_Type': 'Text'
    },
    {
        'Field_Name': 'Calculated_Hours',
        'Description': 'Estimated effort in hours based on field count and complexity',
        'Source': 'Calculated: (TOTAL_All_Fields * 0.5) * Complexity_Multiplier (Simple=1x, Moderate=1.5x, Complex=2.5x)',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Potential_Savings_Hours',
        'Description': 'Potential hours saved through field reuse (40% savings on reusable fields)',
        'Source': 'Calculated: Calculated_Hours * Reuse_Rate * 0.4',
        'Data_Type': 'Number'
    },
    {
        'Field_Name': 'Optimized_Hours',
        'Description': 'Estimated hours after applying reusability optimization',
        'Source': 'Calculated: Calculated_Hours - Potential_Savings_Hours',
        'Data_Type': 'Number'
    }
]

df_key = pd.DataFrame(field_definitions)

# Create summary statistics
print("\n5. Calculating summary statistics...")

summary_stats = []
for category in categories:
    if category == 'If':
        count_col = 'IF_Statement_Count'
        reuse_col = 'IF_Reusable_Count'
    elif category == 'Precedent Script':
        count_col = 'Precedent_Script_Count'
        reuse_col = 'Precedent_Reusable_Count'
    elif category == 'Reflection':
        count_col = 'Reflection_Field_Count'
        reuse_col = 'Reflection_Reusable_Count'
    elif category == 'Search':
        count_col = 'Search_Field_Count'
        reuse_col = 'Search_Reusable_Count'
    elif category == 'Unbound':
        count_col = 'Unbound_Field_Count'
        reuse_col = 'Unbound_Reusable_Count'
    elif category == 'Built In Script':
        count_col = 'BuiltIn_Script_Count'
        reuse_col = 'BuiltIn_Reusable_Count'
    elif category == 'Extended':
        count_col = 'Extended_Field_Count'
        reuse_col = 'Extended_Reusable_Count'
    elif category == 'Scripted':
        count_col = 'Scripted_Field_Count'
        reuse_col = 'Scripted_Reusable_Count'
    
    total = df_results[count_col].sum()
    reusable = df_results[reuse_col].sum()
    
    summary_stats.append({
        'Field_Category': category,
        'Total_Instances': total,
        'Reusable_Instances': reusable,
        'Unique_Instances': total - reusable,
        'Reusability_Rate': f"{(reusable/total*100):.1f}%" if total > 0 else "0.0%",
        'Documents_With_This_Type': (df_results[count_col] > 0).sum(),
        'Average_Per_Document': round(df_results[df_results[count_col] > 0][count_col].mean(), 1) if (df_results[count_col] > 0).sum() > 0 else 0
    })

df_summary = pd.DataFrame(summary_stats)

# Complexity summary
complexity_summary = df_results.groupby('Complexity_Level').agg({
    'Document_Name': 'count',
    'TOTAL_All_Fields': 'mean',
    'Calculated_Hours': ['sum', 'mean'],
    'Optimized_Hours': ['sum', 'mean']
}).round(2)

# Save to Excel
print("\n6. Saving to Excel with clear formatting...")

output_file = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/The336/The336_Field_Analysis_CLEAR.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Field Definitions Key - FIRST SHEET
    df_key.to_excel(writer, sheet_name='FIELD_DEFINITIONS_KEY', index=False)
    
    # Main data
    df_results.to_excel(writer, sheet_name='All_336_Documents', index=False)
    
    # Summary by category
    df_summary.to_excel(writer, sheet_name='Summary_By_Category', index=False)
    
    # Complexity analysis
    complexity_summary.to_excel(writer, sheet_name='Complexity_Summary')
    
    # Top complex documents
    top_complex = df_results.nlargest(20, 'TOTAL_All_Fields')[
        ['Document_Name', 'TOTAL_All_Fields', 'IF_Statement_Count', 
         'Precedent_Script_Count', 'Complexity_Level', 'Calculated_Hours', 'Optimized_Hours']
    ]
    top_complex.to_excel(writer, sheet_name='Top_20_Complex', index=False)
    
    # High reusability documents
    high_reuse = df_results[df_results['TOTAL_Reuse_Rate'] != "0.0%"].copy()
    high_reuse['Reuse_Numeric'] = high_reuse['TOTAL_Reuse_Rate'].str.replace('%', '').astype(float)
    high_reuse = high_reuse.nlargest(20, 'Reuse_Numeric')[
        ['Document_Name', 'TOTAL_All_Fields', 'TOTAL_Reusable_Fields', 
         'TOTAL_Reuse_Rate', 'Potential_Savings_Hours']
    ]
    high_reuse.to_excel(writer, sheet_name='Top_20_Reusable', index=False)

print(f"✓ Saved to {output_file}")

# Print summary
print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

print("\nKEY STATISTICS:")
print(f"  Total Documents: {len(df_results)}")
print(f"  Total Fields: {df_results['TOTAL_All_Fields'].sum():,}")
print(f"  Total Unique Fields: {df_results['TOTAL_Unique_Fields'].sum():,}")
print(f"  Total Reusable Fields: {df_results['TOTAL_Reusable_Fields'].sum():,}")
print(f"  Overall Reusability: {(df_results['TOTAL_Reusable_Fields'].sum()/df_results['TOTAL_All_Fields'].sum()*100):.1f}%")

print("\nCOMPLEXITY DISTRIBUTION:")
for complexity in ['Simple', 'Moderate', 'Complex']:
    count = len(df_results[df_results['Complexity_Level'] == complexity])
    pct = count / len(df_results) * 100
    total_hours = df_results[df_results['Complexity_Level'] == complexity]['Calculated_Hours'].sum()
    print(f"  {complexity:10s}: {count:3d} documents ({pct:5.1f}%) - {total_hours:,.0f} hours")

print("\nEFFORT ESTIMATES:")
print(f"  Base Estimate: {df_results['Calculated_Hours'].sum():,.0f} hours")
print(f"  Potential Savings: {df_results['Potential_Savings_Hours'].sum():,.0f} hours")
print(f"  Optimized Estimate: {df_results['Optimized_Hours'].sum():,.0f} hours")

print("\n" + "=" * 80)
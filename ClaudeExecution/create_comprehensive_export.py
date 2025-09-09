import pandas as pd
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

print("Creating comprehensive export with field analysis and complexity categorization...")

# Load the linked data
df_linked = pd.read_excel('linked_data_comprehensive.xlsx')

# Load SQL data for detailed field analysis
sql_path = Path('../ImportantData/SQLExport')

# Load all SQL data
with open(sql_path / 'dbo_Documents.json', 'r') as f:
    docs_json = json.load(f)
    sql_docs = docs_json.get('data', [])

with open(sql_path / 'dbo_Fields.json', 'r') as f:
    fields_json = json.load(f)
    sql_fields = fields_json.get('data', [])

with open(sql_path / 'dbo_DocumentFields.json', 'r') as f:
    doc_fields_json = json.load(f)
    sql_doc_fields = doc_fields_json.get('data', [])

# Create lookup dictionaries
doc_id_lookup = {}
for doc in sql_docs:
    filename = doc['Filename'].replace('.dot', '').replace('.docx', '')
    doc_id_lookup[filename] = doc['DocumentID']

# Categorize fields by type
field_categories = {}
for field in sql_fields:
    field_id = field['FieldID']
    field_code = field.get('FieldCode', '')
    
    # Determine field category
    if 'IF' in field_code.upper() and 'DOCVARIABLE' in field_code:
        category = 'IF Statements'
    elif 'DOCVARIABLE' in field_code and 'IF' not in field_code.upper():
        category = 'Document Variables'
    elif 'MERGEFIELD' in field_code:
        category = 'Merge Fields'
    elif 'INCLUDETEXT' in field_code:
        category = 'Include Text'
    elif 'REF' in field_code:
        category = 'References'
    elif field_code.strip().startswith('_'):
        category = 'Precedent Scripts'
    else:
        category = 'Other Fields'
    
    field_categories[field_id] = category

# Count field usage across documents
field_usage_count = defaultdict(int)
for doc_field in sql_doc_fields:
    field_id = doc_field['FieldID']
    field_usage_count[field_id] += 1

# Analyze each template
enhanced_data = []

for idx, row in df_linked.iterrows():
    # Start with existing data
    enhanced_row = row.to_dict()
    
    # Initialize field counts
    field_counts = {
        'Total Fields': 0,
        'Unique IF Statements': 0,
        'Unique Document Variables': 0,
        'Unique Merge Fields': 0,
        'Unique Include Text': 0,
        'Unique References': 0,
        'Unique Precedent Scripts': 0,
        'Unique Other Fields': 0,
        'Common IF Statements': 0,
        'Common Document Variables': 0,
        'Common Merge Fields': 0,
        'Common Other Fields': 0
    }
    
    # Get document ID if available
    title = row['ClientReq_Title']
    if title in doc_id_lookup:
        doc_id = doc_id_lookup[title]
        
        # Get all fields for this document
        doc_field_ids = [df['FieldID'] for df in sql_doc_fields if df['DocumentID'] == doc_id]
        
        field_counts['Total Fields'] = len(doc_field_ids)
        
        # Count by category and uniqueness
        for field_id in doc_field_ids:
            category = field_categories.get(field_id, 'Other Fields')
            usage_count = field_usage_count[field_id]
            
            # Determine if field is unique or common
            if usage_count == 1:
                if category == 'IF Statements':
                    field_counts['Unique IF Statements'] += 1
                elif category == 'Document Variables':
                    field_counts['Unique Document Variables'] += 1
                elif category == 'Merge Fields':
                    field_counts['Unique Merge Fields'] += 1
                elif category == 'Include Text':
                    field_counts['Unique Include Text'] += 1
                elif category == 'References':
                    field_counts['Unique References'] += 1
                elif category == 'Precedent Scripts':
                    field_counts['Unique Precedent Scripts'] += 1
                else:
                    field_counts['Unique Other Fields'] += 1
            else:
                # Common fields (used in multiple documents)
                if category == 'IF Statements':
                    field_counts['Common IF Statements'] += 1
                elif category == 'Document Variables':
                    field_counts['Common Document Variables'] += 1
                elif category == 'Merge Fields':
                    field_counts['Common Merge Fields'] += 1
                else:
                    field_counts['Common Other Fields'] += 1
    
    # Add field counts to row
    for key, value in field_counts.items():
        enhanced_row[key] = value
    
    # Calculate complexity score (adjustable formula)
    complexity_score = (
        field_counts['Total Fields'] * 1.0 +
        field_counts['Unique IF Statements'] * 3.0 +
        field_counts['Unique Document Variables'] * 2.0 +
        field_counts['Unique Precedent Scripts'] * 4.0 +
        field_counts['Common IF Statements'] * 0.5 +
        field_counts['Common Document Variables'] * 0.3
    )
    
    enhanced_row['Complexity Score'] = complexity_score
    
    # Categorize complexity (adjustable thresholds)
    if complexity_score == 0:
        calculated_complexity = 'No Data'
    elif complexity_score < 10:
        calculated_complexity = 'Simple'
    elif complexity_score < 30:
        calculated_complexity = 'Moderate'
    else:
        calculated_complexity = 'Complex'
    
    enhanced_row['Calculated Complexity'] = calculated_complexity
    
    # Compare with original complexity if available
    original_complexity = row.get('ClientReq_Complexity', '')
    enhanced_row['Original Complexity'] = original_complexity
    enhanced_row['Complexity Match'] = (calculated_complexity.lower() == original_complexity.lower())
    
    enhanced_data.append(enhanced_row)

# Create DataFrame
df_enhanced = pd.DataFrame(enhanced_data)

# Create Excel writer with multiple sheets
with pd.ExcelWriter('EstimateDoc_Comprehensive_Analysis.xlsx', engine='openpyxl') as writer:
    
    # Sheet 1: Full Data
    df_enhanced.to_excel(writer, sheet_name='Full Analysis', index=False)
    
    # Sheet 2: Summary Statistics
    summary_stats = {
        'Metric': [],
        'Value': []
    }
    
    summary_stats['Metric'].extend([
        'Total Templates',
        'Templates with Field Data',
        'Templates without Field Data',
        'Average Fields per Template',
        'Average Unique IF Statements',
        'Average Common IF Statements',
        'Simple Templates',
        'Moderate Templates',
        'Complex Templates',
        'No Data Templates'
    ])
    
    templates_with_data = df_enhanced[df_enhanced['Total Fields'] > 0]
    
    summary_stats['Value'].extend([
        len(df_enhanced),
        len(templates_with_data),
        len(df_enhanced[df_enhanced['Total Fields'] == 0]),
        templates_with_data['Total Fields'].mean() if len(templates_with_data) > 0 else 0,
        templates_with_data['Unique IF Statements'].mean() if len(templates_with_data) > 0 else 0,
        templates_with_data['Common IF Statements'].mean() if len(templates_with_data) > 0 else 0,
        len(df_enhanced[df_enhanced['Calculated Complexity'] == 'Simple']),
        len(df_enhanced[df_enhanced['Calculated Complexity'] == 'Moderate']),
        len(df_enhanced[df_enhanced['Calculated Complexity'] == 'Complex']),
        len(df_enhanced[df_enhanced['Calculated Complexity'] == 'No Data'])
    ])
    
    df_summary = pd.DataFrame(summary_stats)
    df_summary.to_excel(writer, sheet_name='Summary Statistics', index=False)
    
    # Sheet 3: Complexity Configuration
    config_data = {
        'Configuration': [
            'Simple Threshold (< this value)',
            'Moderate Threshold (< this value)',
            'Complex Threshold (>= previous value)',
            '',
            'Field Weights:',
            'Total Fields Weight',
            'Unique IF Statements Weight',
            'Unique Document Variables Weight',
            'Unique Precedent Scripts Weight',
            'Common IF Statements Weight',
            'Common Document Variables Weight'
        ],
        'Current Value': [
            10,
            30,
            30,
            '',
            '',
            1.0,
            3.0,
            2.0,
            4.0,
            0.5,
            0.3
        ],
        'Description': [
            'Templates with score below this are Simple',
            'Templates with score below this are Moderate',
            'Templates with score at or above are Complex',
            '',
            '',
            'Multiplier for total field count',
            'Multiplier for unique IF statements',
            'Multiplier for unique document variables',
            'Multiplier for unique precedent scripts',
            'Multiplier for common IF statements',
            'Multiplier for common document variables'
        ]
    }
    
    df_config = pd.DataFrame(config_data)
    df_config.to_excel(writer, sheet_name='Complexity Configuration', index=False)
    
    # Sheet 4: Field Category Breakdown
    category_breakdown = []
    for category in ['IF Statements', 'Document Variables', 'Merge Fields', 'Precedent Scripts', 'Other Fields']:
        unique_col = f'Unique {category}'
        common_col = f'Common {category}'
        
        if unique_col in df_enhanced.columns:
            unique_sum = df_enhanced[unique_col].sum()
        else:
            unique_sum = 0
            
        if common_col in df_enhanced.columns:
            common_sum = df_enhanced[common_col].sum()
        else:
            common_sum = 0
            
        category_breakdown.append({
            'Field Category': category,
            'Total Unique Instances': unique_sum,
            'Total Common Instances': common_sum,
            'Total Instances': unique_sum + common_sum
        })
    
    df_categories = pd.DataFrame(category_breakdown)
    df_categories.to_excel(writer, sheet_name='Field Categories', index=False)

print(f"\nExport complete! Created 'EstimateDoc_Comprehensive_Analysis.xlsx' with:")
print(f"  - {len(df_enhanced)} template records")
print(f"  - {len(templates_with_data)} templates with field data")
print(f"  - Field categorization and complexity calculations")
print(f"  - Configurable complexity thresholds")

# Also save as JSON for database import
export_json = {
    'templates': df_enhanced.to_dict('records'),
    'summary': summary_stats,
    'configuration': config_data,
    'field_categories': category_breakdown
}

with open('EstimateDoc_Export.json', 'w') as f:
    json.dump(export_json, f, indent=2, default=str)

print(f"  - Also saved as 'EstimateDoc_Export.json' for database import")
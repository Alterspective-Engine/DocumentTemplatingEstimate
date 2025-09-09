import pymssql
import pandas as pd
import json
from pathlib import Path
import re
from collections import defaultdict

print("=" * 80)
print("COMPREHENSIVE DATABASE ANALYSIS WITH CORRECT FIELD CATEGORIES")
print("=" * 80)

# Database connection parameters
server = 'mosmar-cip.database.windows.net'
database = 'Mosmar_CIP_Dev'
username = 'mosmaradmin'
password = 'M0sM4r.2021'

try:
    print("\nConnecting to database...")
    conn = pymssql.connect(
        server=server,
        user=username,
        password=password,
        database=database,
        tds_version='7.4'
    )
    cursor = conn.cursor(as_dict=True)
    print("✓ Successfully connected to database")
    
    # Load Client Requirements first
    print("\nLoading Client Requirements...")
    df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
    print(f"✓ Loaded {len(df_client)} client requirements")
    
    # Get all documents from database
    print("\nRetrieving documents from database...")
    cursor.execute("""
        SELECT DocumentID, Filename
        FROM dbo.Documents
    """)
    all_docs = cursor.fetchall()
    print(f"✓ Retrieved {len(all_docs)} documents")
    
    # Create lookup dictionary for matching
    doc_lookup = {}
    doc_lookup_by_id = {}
    
    for doc in all_docs:
        doc_id = doc['DocumentID']
        filename = doc['Filename']
        
        if filename:
            # Remove extension and convert to lowercase for matching
            base_name = filename.replace('.dot', '').replace('.docx', '').lower()
            doc_lookup[base_name] = {
                'DocumentID': doc_id,
                'Filename': filename
            }
            doc_lookup_by_id[doc_id] = {
                'Filename': filename,
                'BaseName': base_name
            }
    
    print(f"Created lookup for {len(doc_lookup)} documents")
    
    # Now run the comprehensive query from BecInfo with field categorization
    print("\n" + "=" * 80)
    print("ANALYZING FIELDS WITH CORRECT CATEGORIZATION")
    print("=" * 80)
    
    print("\nExecuting comprehensive field analysis query...")
    cursor.execute("""
        SELECT
            DOC.DocumentID,
            DOC.Filename,
            F.FieldID,
            F.FieldCode,
            F.FieldResult,
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
        LEFT JOIN
            DocumentFields DF ON DOC.DocumentID = DF.DocumentID
        LEFT JOIN
            Fields F ON F.FieldID = DF.FieldID
        WHERE
            DF.FieldID IS NOT NULL
    """)
    
    all_field_data = cursor.fetchall()
    print(f"✓ Retrieved {len(all_field_data)} field mappings")
    
    # Analyze field categories
    category_counts = defaultdict(int)
    doc_field_profiles = defaultdict(lambda: defaultdict(int))
    unique_fields_by_category = defaultdict(set)
    
    for row in all_field_data:
        doc_id = row['DocumentID']
        field_id = row['FieldID']
        category = row['field_category']
        count = row['Count'] or 1
        
        # Track overall category counts
        category_counts[category] += 1
        unique_fields_by_category[category].add(field_id)
        
        # Build per-document profiles
        doc_field_profiles[doc_id][category] += count
        doc_field_profiles[doc_id]['Total'] += count
        doc_field_profiles[doc_id]['UniqueFields'] += 1
    
    print("\n" + "=" * 80)
    print("FIELD CATEGORY STATISTICS")
    print("=" * 80)
    
    print("\nField distribution by category:")
    for category in sorted(category_counts.keys()):
        total_instances = category_counts[category]
        unique_fields = len(unique_fields_by_category[category])
        print(f"  {category:20s}: {unique_fields:,} unique fields, {total_instances:,} total instances")
    
    # Calculate effort estimates based on BecInfo guidance
    effort_minutes = {
        'Reflection': 5,
        'Extended': 5,
        'Unbound': 5,  # Plus 15 for form creation
        'Search': 10,
        'If Statement': 15,
        'Built In Script': 20,  # Estimate since we can't see the code
        'Scripted': 30,  # Complex - needs investigation
        'Precedent Script': 30  # Complex - needs investigation
    }
    
    print("\nEffort estimates per field type (minutes):")
    for cat, mins in effort_minutes.items():
        print(f"  {cat:20s}: {mins} minutes")
    
    # Match client requirements with database documents
    print("\n" + "=" * 80)
    print("MATCHING CLIENT REQUIREMENTS WITH DATABASE")
    print("=" * 80)
    
    comprehensive_data = []
    matched_count = 0
    
    for idx, row in df_client.iterrows():
        title = row['Current Title']
        title_lower = title.lower()
        
        result = {
            'ClientTitle': title,
            'Description': row['Description'],
            'OriginalComplexity': row['Complexity'],
            'HasSQLData': False,
            'DocumentID': None,
            'Filename': None,
            'TotalFieldInstances': 0,
            'UniqueFields': 0,
            'EstimatedMinutes': 0,
            'EstimatedHours': 0
        }
        
        # Initialize category columns
        for category in effort_minutes.keys():
            result[f'{category}_Count'] = 0
            result[f'{category}_Minutes'] = 0
        
        # Check if we have SQL data for this document
        if title_lower in doc_lookup:
            matched_count += 1
            doc_id = doc_lookup[title_lower]['DocumentID']
            result['HasSQLData'] = True
            result['DocumentID'] = doc_id
            result['Filename'] = doc_lookup[title_lower]['Filename']
            
            # Get field profile for this document
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
                    total_minutes += 15  # Additional time for form creation
                
                result['EstimatedMinutes'] = total_minutes
                result['EstimatedHours'] = round(total_minutes / 60, 2)
        
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
    
    # Statistics
    print(f"\nMatching Results:")
    print(f"  Total client requirements: {len(df_client)}")
    print(f"  Matched with SQL data: {matched_count} ({matched_count/len(df_client)*100:.1f}%)")
    print(f"  No SQL data: {len(df_client) - matched_count}")
    
    docs_with_data = df_comprehensive[df_comprehensive['HasSQLData'] == True]
    if len(docs_with_data) > 0:
        print(f"\nFor documents with SQL data:")
        print(f"  Average estimated hours: {docs_with_data['EstimatedHours'].mean():.2f}")
        print(f"  Min estimated hours: {docs_with_data['EstimatedHours'].min():.2f}")
        print(f"  Max estimated hours: {docs_with_data['EstimatedHours'].max():.2f}")
        
        print(f"\nComplexity distribution (calculated):")
        complexity_dist = df_comprehensive['CalculatedComplexity'].value_counts()
        for complexity, count in complexity_dist.items():
            print(f"  {complexity}: {count} ({count/len(df_comprehensive)*100:.1f}%)")
    
    # Get additional statistics for reporting
    cursor.execute("SELECT COUNT(DISTINCT DocumentID) FROM DocumentFields")
    docs_with_fields = cursor.fetchone()['COUNT']
    
    cursor.execute("SELECT COUNT(*) FROM Fields")
    total_fields = cursor.fetchone()['COUNT']
    
    cursor.execute("SELECT COUNT(*) FROM DocumentFields")
    total_mappings = cursor.fetchone()['COUNT']
    
    print(f"\nDatabase Statistics:")
    print(f"  Total documents: {len(all_docs)}")
    print(f"  Documents with field data: {docs_with_fields}")
    print(f"  Total unique fields: {total_fields}")
    print(f"  Total field mappings: {total_mappings}")
    
    # Save comprehensive analysis
    output_file = 'CORRECTED_EstimateDoc_Analysis.xlsx'
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Main analysis sheet
        df_comprehensive.to_excel(writer, sheet_name='Full Analysis', index=False)
        
        # Summary statistics sheet
        summary_data = {
            'Metric': [
                'Total Client Requirements',
                'Requirements with SQL Data',
                'Match Rate',
                'Average Estimated Hours',
                'Total Documents in DB',
                'Documents with Fields',
                'Total Unique Fields',
                'Total Field Mappings'
            ],
            'Value': [
                len(df_client),
                matched_count,
                f"{matched_count/len(df_client)*100:.1f}%",
                f"{docs_with_data['EstimatedHours'].mean():.2f}" if len(docs_with_data) > 0 else "0",
                len(all_docs),
                docs_with_fields,
                total_fields,
                total_mappings
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Field category breakdown
        category_data = []
        for category in sorted(effort_minutes.keys()):
            category_data.append({
                'Category': category,
                'Unique Fields': len(unique_fields_by_category[category]),
                'Total Instances': category_counts[category],
                'Minutes per Field': effort_minutes[category],
                'Description': get_category_description(category)
            })
        df_categories = pd.DataFrame(category_data)
        df_categories.to_excel(writer, sheet_name='Field Categories', index=False)
        
        # Complexity thresholds
        threshold_data = {
            'Complexity': ['Simple', 'Moderate', 'Complex'],
            'Hours Range': ['< 2 hours', '2-8 hours', '> 8 hours'],
            'Count': [
                len(df_comprehensive[df_comprehensive['CalculatedComplexity'] == 'Simple']),
                len(df_comprehensive[df_comprehensive['CalculatedComplexity'] == 'Moderate']),
                len(df_comprehensive[df_comprehensive['CalculatedComplexity'] == 'Complex'])
            ]
        }
        df_thresholds = pd.DataFrame(threshold_data)
        df_thresholds.to_excel(writer, sheet_name='Complexity Distribution', index=False)
    
    print(f"\n✓ Saved comprehensive analysis to {output_file}")
    
    # Save JSON summary
    json_summary = {
        'analysis_date': pd.Timestamp.now().isoformat(),
        'database_connection': 'SUCCESS',
        'client_requirements': len(df_client),
        'matched_requirements': matched_count,
        'match_rate': f"{matched_count/len(df_client)*100:.1f}%",
        'field_categories': {
            cat: {
                'unique_fields': len(unique_fields_by_category[cat]),
                'total_instances': category_counts[cat],
                'effort_minutes': effort_minutes[cat]
            }
            for cat in effort_minutes.keys()
        },
        'complexity_distribution': threshold_data,
        'database_stats': {
            'total_documents': len(all_docs),
            'documents_with_fields': docs_with_fields,
            'total_unique_fields': total_fields,
            'total_field_mappings': total_mappings
        }
    }
    
    with open('corrected_analysis_summary.json', 'w') as f:
        json.dump(json_summary, f, indent=2)
    
    print("✓ Saved summary to corrected_analysis_summary.json")
    
    conn.close()
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

def get_category_description(category):
    """Return description for each field category based on BecInfo"""
    descriptions = {
        'Search': 'Selecting from a list (e.g., participants, clients)',
        'Reflection': 'Built-in fields that reflect through object model',
        'If Statement': 'Conditional display logic',
        'Built In Script': 'MatterSphere helper scripts (code not visible)',
        'Extended': 'Form builder fields linked to object layer',
        'Scripted': 'C# scripts that output strings',
        'Unbound': 'Document questionnaire fields (not stored in DB)',
        'Precedent Script': 'C# scripts specific to the precedent'
    }
    return descriptions.get(category, '')
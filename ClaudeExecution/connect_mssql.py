import subprocess
import sys
import pandas as pd
import json
from pathlib import Path
import re
from collections import defaultdict

print("=" * 80)
print("CONNECTING TO SQL SERVER DATABASE")
print("=" * 80)

# First try to install required packages
print("\nChecking for required packages...")
try:
    import pymssql
    print("✓ pymssql is installed")
except ImportError:
    print("Installing pymssql...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pymssql"])
    import pymssql

# Database connection parameters from .env
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
    cursor = conn.cursor()
    print("✓ Successfully connected to database")
    
    # First, explore the database schema
    print("\n" + "=" * 80)
    print("1. EXPLORING DATABASE SCHEMA")
    print("=" * 80)
    
    # Get all tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    
    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables in database")
    
    # Group by schema
    schemas = defaultdict(list)
    for schema, table in tables:
        schemas[schema].append(table)
    
    for schema, table_list in schemas.items():
        print(f"\nSchema '{schema}': {len(table_list)} tables")
        for table in table_list[:10]:  # Show first 10 tables
            print(f"  - {table}")
        if len(table_list) > 10:
            print(f"  ... and {len(table_list) - 10} more")
    
    # Look for relevant tables
    print("\n" + "=" * 80)
    print("2. SEARCHING FOR RELEVANT TABLES")
    print("=" * 80)
    
    # Search for document/field related tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND (
            TABLE_NAME LIKE '%Document%' 
            OR TABLE_NAME LIKE '%Field%'
            OR TABLE_NAME LIKE '%Template%'
            OR TABLE_NAME LIKE '%Precedent%'
        )
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    
    relevant_tables = cursor.fetchall()
    print(f"\nFound {len(relevant_tables)} potentially relevant tables:")
    for schema, table in relevant_tables:
        print(f"  {schema}.{table}")
        
        # Get row count for each
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{table}]")
            row_count = cursor.fetchone()[0]
            print(f"    → {row_count:,} rows")
        except:
            print(f"    → Unable to count rows")
    
    # Examine the Documents table structure
    print("\n" + "=" * 80)
    print("3. EXAMINING DOCUMENTS TABLE")
    print("=" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Documents'
        ORDER BY ORDINAL_POSITION
    """)
    
    doc_columns = cursor.fetchall()
    print("\nDocuments table structure:")
    for col_name, data_type, max_len in doc_columns:
        if max_len:
            print(f"  - {col_name}: {data_type}({max_len})")
        else:
            print(f"  - {col_name}: {data_type}")
    
    # Get sample documents
    cursor.execute("""
        SELECT TOP 20 DocumentID, Filename, FileExtension 
        FROM dbo.Documents
        ORDER BY DocumentID
    """)
    
    docs_sample = cursor.fetchall()
    print(f"\nSample documents (first 10):")
    for doc_id, filename, ext in docs_sample[:10]:
        print(f"  ID {doc_id}: {filename} ({ext})")
    
    # Get total document count
    cursor.execute("SELECT COUNT(*) FROM dbo.Documents")
    total_docs = cursor.fetchone()[0]
    print(f"\nTotal documents in database: {total_docs:,}")
    
    # Get all document filenames for matching
    cursor.execute("""
        SELECT DocumentID, Filename, FileExtension
        FROM dbo.Documents
    """)
    
    all_docs = cursor.fetchall()
    
    # Load Client Requirements
    df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
    print(f"\n\nLoaded {len(df_client)} client requirements")
    
    # Create lookup dictionary
    doc_lookup = {}
    doc_lookup_by_id = {}
    for doc_id, filename, ext in all_docs:
        if filename:
            # Remove extension if present in filename
            base_name = filename.replace('.dot', '').replace('.docx', '').lower()
            doc_lookup[base_name] = {
                'DocumentID': doc_id,
                'Filename': filename,
                'Extension': ext
            }
            doc_lookup_by_id[doc_id] = {
                'Filename': filename,
                'BaseName': base_name,
                'Extension': ext
            }
    
    print(f"Created lookup for {len(doc_lookup)} documents")
    
    # Match client requirements with documents
    matches = []
    no_matches = []
    
    for idx, row in df_client.iterrows():
        title = row['Current Title'].lower()
        
        if title in doc_lookup:
            matches.append({
                'ClientTitle': row['Current Title'],
                'Description': row['Description'],
                'Complexity': row['Complexity'],
                'DocumentID': doc_lookup[title]['DocumentID'],
                'Filename': doc_lookup[title]['Filename']
            })
        else:
            no_matches.append(row['Current Title'])
    
    print(f"\nMatching results:")
    print(f"  Matched: {len(matches)} ({len(matches)/len(df_client)*100:.1f}%)")
    print(f"  Not matched: {len(no_matches)} ({len(no_matches)/len(df_client)*100:.1f}%)")
    
    # Examine Fields table
    print("\n" + "=" * 80)
    print("4. EXAMINING FIELDS TABLE")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Fields")
    total_fields = cursor.fetchone()[0]
    print(f"Total fields in database: {total_fields:,}")
    
    # Get sample fields to understand structure
    cursor.execute("""
        SELECT TOP 5 FieldID, FieldCode, FieldResult
        FROM dbo.Fields
    """)
    
    sample_fields = cursor.fetchall()
    print("\nSample fields:")
    for fid, fcode, fresult in sample_fields:
        print(f"  ID {fid}: {fcode[:50]}...")
    
    # Check DocumentFields mapping
    print("\n" + "=" * 80)
    print("5. ANALYZING FIELD DISTRIBUTION")
    print("=" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM dbo.DocumentFields")
    total_mappings = cursor.fetchone()[0]
    print(f"Total document-field mappings: {total_mappings:,}")
    
    # Get documents with most fields
    cursor.execute("""
        SELECT TOP 10 df.DocumentID, COUNT(*) as FieldCount, SUM(df.Count) as TotalInstances
        FROM dbo.DocumentFields df
        GROUP BY df.DocumentID
        ORDER BY COUNT(*) DESC
    """)
    
    top_docs = cursor.fetchall()
    print("\nDocuments with most fields:")
    for doc_id, field_count, total_instances in top_docs:
        doc_info = doc_lookup_by_id.get(doc_id, {})
        filename = doc_info.get('Filename', 'Unknown')
        print(f"  ID {doc_id} ({filename}): {field_count} unique fields, {total_instances} total instances")
    
    # Now analyze ALL matched documents
    print("\n" + "=" * 80)
    print("6. COMPREHENSIVE FIELD ANALYSIS FOR ALL DOCUMENTS")
    print("=" * 80)
    
    # Get all fields with their codes for categorization
    cursor.execute("""
        SELECT FieldID, FieldCode
        FROM dbo.Fields
    """)
    
    all_fields = cursor.fetchall()
    field_categories = {}
    
    for field_id, field_code in all_fields:
        if field_code:
            # Categorize field
            if re.search(r'\bIF\b', str(field_code), re.IGNORECASE):
                category = 'IF Statements'
            elif 'DOCVARIABLE' in str(field_code):
                category = 'Document Variables'
            elif 'MERGEFIELD' in str(field_code):
                category = 'Merge Fields'
            elif 'INCLUDETEXT' in str(field_code):
                category = 'Include Text'
            elif 'REF' in str(field_code) and 'MERGEFIELD' not in str(field_code):
                category = 'References'
            else:
                category = 'Other'
            
            field_categories[field_id] = category
    
    print(f"Categorized {len(field_categories)} fields")
    
    # Category distribution
    cat_counts = defaultdict(int)
    for cat in field_categories.values():
        cat_counts[cat] += 1
    
    print("\nField category distribution:")
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat}: {count:,} fields")
    
    # Now process ALL documents with field data
    cursor.execute("""
        SELECT DocumentID, FieldID, Count
        FROM dbo.DocumentFields
    """)
    
    all_mappings = cursor.fetchall()
    
    # Build document field profiles
    doc_profiles = defaultdict(lambda: defaultdict(int))
    
    for doc_id, field_id, count in all_mappings:
        category = field_categories.get(field_id, 'Other')
        doc_profiles[doc_id][category] += count
        doc_profiles[doc_id]['Total'] += count
    
    print(f"\nProcessed field data for {len(doc_profiles)} documents")
    
    # Create comprehensive analysis for client requirements
    comprehensive_data = []
    
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
            'TotalFieldInstances': 0
        }
        
        # Initialize category columns
        for category in cat_counts.keys():
            result[f'{category}_Count'] = 0
        
        # Check if we have SQL data
        if title_lower in doc_lookup:
            doc_id = doc_lookup[title_lower]['DocumentID']
            result['HasSQLData'] = True
            result['DocumentID'] = doc_id
            result['Filename'] = doc_lookup[title_lower]['Filename']
            
            # Get field profile
            if doc_id in doc_profiles:
                profile = doc_profiles[doc_id]
                result['TotalFieldInstances'] = profile['Total']
                
                for category in cat_counts.keys():
                    result[f'{category}_Count'] = profile.get(category, 0)
        
        comprehensive_data.append(result)
    
    # Convert to DataFrame
    df_comprehensive = pd.DataFrame(comprehensive_data)
    
    # Calculate statistics
    docs_with_data = df_comprehensive[df_comprehensive['HasSQLData'] == True]
    print(f"\n" + "=" * 80)
    print("7. FINAL STATISTICS")
    print("=" * 80)
    print(f"Total client requirements: {len(df_comprehensive)}")
    print(f"Requirements with SQL data: {len(docs_with_data)} ({len(docs_with_data)/len(df_comprehensive)*100:.1f}%)")
    print(f"Requirements without SQL data: {len(df_comprehensive) - len(docs_with_data)}")
    
    if len(docs_with_data) > 0:
        print(f"\nFor documents with SQL data:")
        print(f"  Average total field instances: {docs_with_data['TotalFieldInstances'].mean():.1f}")
        print(f"  Min field instances: {docs_with_data['TotalFieldInstances'].min()}")
        print(f"  Max field instances: {docs_with_data['TotalFieldInstances'].max()}")
        
        print(f"\nAverage by category:")
        for category in cat_counts.keys():
            col_name = f'{category}_Count'
            if col_name in docs_with_data.columns:
                avg = docs_with_data[col_name].mean()
                if avg > 0:
                    print(f"  {category}: {avg:.1f}")
    
    # Save comprehensive analysis
    df_comprehensive.to_excel('FINAL_comprehensive_analysis.xlsx', index=False)
    print(f"\n✓ Saved comprehensive analysis to FINAL_comprehensive_analysis.xlsx")
    
    # Save summary statistics
    summary = {
        'database_connection': 'SUCCESS',
        'total_documents_in_db': total_docs,
        'total_fields_in_db': total_fields,
        'total_mappings_in_db': total_mappings,
        'client_requirements': len(df_client),
        'matched_requirements': len(docs_with_data),
        'match_rate': f"{len(docs_with_data)/len(df_comprehensive)*100:.1f}%",
        'field_categories': dict(cat_counts),
        'documents_with_field_data': len(doc_profiles)
    }
    
    with open('database_analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Saved summary to database_analysis_summary.json")
    
    conn.close()
    print("\n" + "=" * 80)
    print("DATABASE ANALYSIS COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
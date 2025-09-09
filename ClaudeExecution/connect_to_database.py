import pyodbc
import pandas as pd
import json
from pathlib import Path
import re
from collections import defaultdict

print("=" * 80)
print("CONNECTING TO SQL SERVER DATABASE")
print("=" * 80)

# Database connection parameters from .env
server = 'mosmar-cip.database.windows.net,1433'
database = 'Mosmar_CIP_Dev'
username = 'mosmaradmin'
password = 'M0sM4r.2021'

# Create connection string
conn_str = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes'

try:
    print("\nConnecting to database...")
    conn = pyodbc.connect(conn_str)
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
        SELECT TABLE_SCHEMA, TABLE_NAME, 
               (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE c.TABLE_SCHEMA = t.TABLE_SCHEMA 
                AND c.TABLE_NAME = t.TABLE_NAME) as COLUMN_COUNT
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
    for schema, table, col_count in relevant_tables:
        print(f"  {schema}.{table} ({col_count} columns)")
        
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
        SELECT TOP 20 * FROM dbo.Documents
        ORDER BY DocumentID
    """)
    
    # Get column names
    columns = [column[0] for column in cursor.description]
    print(f"\nDocuments table columns: {columns}")
    
    # Convert to DataFrame for easier viewing
    docs_sample = cursor.fetchall()
    df_docs = pd.DataFrame.from_records(docs_sample, columns=columns)
    
    print(f"\nSample documents (first 5):")
    for idx, row in df_docs.head().iterrows():
        print(f"  ID {row['DocumentID']}: {row.get('Filename', 'N/A')}")
    
    # Get total document count
    cursor.execute("SELECT COUNT(*) FROM dbo.Documents")
    total_docs = cursor.fetchone()[0]
    print(f"\nTotal documents in database: {total_docs:,}")
    
    # Examine Fields table
    print("\n" + "=" * 80)
    print("4. EXAMINING FIELDS TABLE")
    print("=" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Fields'
        ORDER BY ORDINAL_POSITION
    """)
    
    field_columns = cursor.fetchall()
    print("\nFields table structure:")
    for col_name, data_type, max_len in field_columns:
        if max_len:
            print(f"  - {col_name}: {data_type}({max_len})")
        else:
            print(f"  - {col_name}: {data_type}")
    
    # Get field statistics
    cursor.execute("SELECT COUNT(*) FROM dbo.Fields")
    total_fields = cursor.fetchone()[0]
    print(f"\nTotal fields in database: {total_fields:,}")
    
    # Check if there's a Category column in Fields
    cursor.execute("""
        SELECT TOP 1 * FROM dbo.Fields
    """)
    field_sample = cursor.fetchone()
    field_cols = [column[0] for column in cursor.description]
    print(f"\nFields table columns: {field_cols}")
    
    # Examine DocumentFields mapping
    print("\n" + "=" * 80)
    print("5. EXAMINING DOCUMENTFIELDS MAPPING")
    print("=" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DocumentFields'
        ORDER BY ORDINAL_POSITION
    """)
    
    docfield_columns = cursor.fetchall()
    print("\nDocumentFields table structure:")
    for col_name, data_type in docfield_columns:
        print(f"  - {col_name}: {data_type}")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.DocumentFields")
    total_mappings = cursor.fetchone()[0]
    print(f"\nTotal document-field mappings: {total_mappings:,}")
    
    # Now let's match Client Requirements with Documents
    print("\n" + "=" * 80)
    print("6. MATCHING CLIENT REQUIREMENTS WITH DATABASE")
    print("=" * 80)
    
    # Load Client Requirements
    df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
    print(f"\nLoaded {len(df_client)} client requirements")
    
    # Get all documents from database
    cursor.execute("""
        SELECT DocumentID, Filename, FileExtension
        FROM dbo.Documents
    """)
    
    all_docs = cursor.fetchall()
    print(f"Retrieved {len(all_docs)} documents from database")
    
    # Create lookup dictionary
    doc_lookup = {}
    for doc_id, filename, ext in all_docs:
        if filename:
            # Remove extension if present in filename
            base_name = filename.replace('.dot', '').replace('.docx', '').lower()
            doc_lookup[base_name] = {
                'DocumentID': doc_id,
                'Filename': filename,
                'Extension': ext
            }
    
    # Match client requirements with documents
    matches = []
    no_matches = []
    
    for idx, row in df_client.iterrows():
        title = row['Current Title'].lower()
        
        if title in doc_lookup:
            matches.append({
                'ClientTitle': row['Current Title'],
                'DocumentID': doc_lookup[title]['DocumentID'],
                'Filename': doc_lookup[title]['Filename']
            })
        else:
            no_matches.append(row['Current Title'])
    
    print(f"\nMatching results:")
    print(f"  Matched: {len(matches)} ({len(matches)/len(df_client)*100:.1f}%)")
    print(f"  Not matched: {len(no_matches)} ({len(no_matches)/len(df_client)*100:.1f}%)")
    
    if matches:
        print(f"\nSample matches:")
        for match in matches[:5]:
            print(f"  {match['ClientTitle']} → {match['Filename']} (ID: {match['DocumentID']})")
    
    # For matched documents, get field breakdown
    print("\n" + "=" * 80)
    print("7. ANALYZING FIELD CATEGORIES FOR MATCHED DOCUMENTS")
    print("=" * 80)
    
    if matches:
        # Get field data for a sample matched document
        sample_doc_id = matches[0]['DocumentID']
        
        cursor.execute("""
            SELECT f.FieldID, f.FieldCode, f.FieldResult, df.Count
            FROM dbo.DocumentFields df
            JOIN dbo.Fields f ON df.FieldID = f.FieldID
            WHERE df.DocumentID = ?
        """, sample_doc_id)
        
        sample_fields = cursor.fetchall()
        print(f"\nDocument '{matches[0]['ClientTitle']}' has {len(sample_fields)} field mappings")
        
        # Categorize fields
        categories = defaultdict(int)
        for field_id, field_code, field_result, count in sample_fields[:10]:
            if field_code:
                if re.search(r'\bIF\b', field_code, re.IGNORECASE):
                    categories['IF Statements'] += count
                elif 'DOCVARIABLE' in field_code:
                    categories['Document Variables'] += count
                elif 'MERGEFIELD' in field_code:
                    categories['Merge Fields'] += count
                else:
                    categories['Other'] += count
        
        print("\nField categories for this document:")
        for cat, cnt in categories.items():
            print(f"  {cat}: {cnt}")
    
    # Check if there are additional linking tables
    print("\n" + "=" * 80)
    print("8. CHECKING FOR ADDITIONAL LINKING MECHANISMS")
    print("=" * 80)
    
    # Look for precedent or template tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND (TABLE_NAME LIKE '%Prec%' OR TABLE_NAME LIKE '%Template%')
    """)
    
    prec_tables = cursor.fetchall()
    if prec_tables:
        print(f"\nFound {len(prec_tables)} precedent/template related tables:")
        for table in prec_tables:
            print(f"  - {table[0]}")
            
            # Check if any contain linking information
            cursor.execute(f"""
                SELECT TOP 1 * FROM dbo.{table[0]}
            """)
            sample = cursor.fetchone()
            if sample:
                cols = [column[0] for column in cursor.description]
                print(f"    Columns: {', '.join(cols[:5])}...")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    conn.close()
    
except Exception as e:
    print(f"\nError connecting to database: {e}")
    print("\nTrying alternative connection method...")
    
    # Try with different driver
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes'
        conn = pyodbc.connect(conn_str)
        print("✓ Connected with alternative driver")
        conn.close()
    except Exception as e2:
        print(f"Alternative connection also failed: {e2}")
        print("\nPlease ensure you have SQL Server ODBC driver installed")
        print("Install with: brew install microsoft/mssql-release/msodbcsql17")
#!/usr/bin/env python3
"""
Download data from SQL Server to JSON files
"""

import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection details from .env
SERVER = os.getenv('DB_SERVER', 'mosmar-cip.database.windows.net,1433')
DATABASE = os.getenv('DB_NAME', 'Mosmar_CIP_Dev')
USERNAME = os.getenv('DB_USER', 'mosmaradmin')
PASSWORD = os.getenv('DB_PASSWORD')

def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    raise TypeError(f"Type {type(obj)} not serializable")

def get_connection():
    """Create and return database connection"""
    if not PASSWORD:
        raise ValueError("DB_PASSWORD not found in environment variables")
    
    connection_string = (
        f'DRIVER={{ODBC Driver 18 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'UID={USERNAME};'
        f'PWD={PASSWORD};'
        f'TrustServerCertificate=yes;'
    )
    return pyodbc.connect(connection_string)

def fetch_table_data(cursor, table_name):
    """Fetch all data from a table"""
    print(f"Fetching data from {table_name}...")
    cursor.execute(f"SELECT * FROM {table_name}")
    
    # Get column names
    columns = [column[0] for column in cursor.description]
    
    # Fetch all rows
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    data = []
    for row in rows:
        row_dict = {}
        for i, column in enumerate(columns):
            value = row[i]
            row_dict[column] = value
        data.append(row_dict)
    
    return data

def fetch_field_analysis(cursor):
    """Fetch the field analysis query from BecInfo.txt"""
    print("Fetching field analysis data...")
    
    query = """
    SELECT
        DOC.documentid,
        filename,
        fieldcode,
        fieldresult,
        CASE
            WHEN fieldcode LIKE '%UDSCH%' THEN 'Search'
            WHEN fieldcode LIKE '%~%' THEN 'Reflection'
            WHEN fieldcode LIKE '%IF%' THEN 'If'
            WHEN fieldcode LIKE '%DOCVARIABLE "#%' THEN 'Built In Script'
            WHEN fieldcode LIKE '%$$%' THEN 'Extended'
            WHEN fieldcode LIKE '%SCR%' THEN 'Scripted'
            WHEN fieldcode LIKE '%[_]%' THEN 'Unbound'
            ELSE 'Precedent Script'
        END AS field_category
    FROM
        documents DOC
    LEFT JOIN
        DocumentFields DF ON DOC.DocumentID = DF.DocumentID
    LEFT JOIN
        fields F ON F.fieldid = DF.FieldID;
    """
    
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        row_dict = {}
        for i, column in enumerate(columns):
            value = row[i]
            row_dict[column] = value
        data.append(row_dict)
    
    return data

def save_to_json(data, filename):
    """Save data to JSON file"""
    filepath = os.path.join('newSQL', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=json_serial, ensure_ascii=False)
    print(f"Saved {len(data)} records to {filename}")

def main():
    """Main function"""
    try:
        # Connect to database
        print(f"\nConnecting to {SERVER}/{DATABASE}...")
        conn = get_connection()
        cursor = conn.cursor()
        print("Connected successfully!\n")
        
        # Test connection
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"SQL Server Version: {version.split('\\n')[0]}\n")
        
        # Fetch and save core tables
        tables = ['Documents', 'Fields', 'DocumentFields']
        
        for table in tables:
            try:
                data = fetch_table_data(cursor, table)
                save_to_json(data, f"{table.lower()}.json")
            except Exception as e:
                print(f"Error fetching {table}: {e}")
        
        # Fetch and save field analysis
        try:
            field_analysis = fetch_field_analysis(cursor)
            save_to_json(field_analysis, "field_analysis.json")
        except Exception as e:
            print(f"Error fetching field analysis: {e}")
        
        # Get table schemas
        print("\nFetching table schemas...")
        schema_query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME IN ('Documents', 'Fields', 'DocumentFields')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        cursor.execute(schema_query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        schemas = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                row_dict[column] = row[i]
            schemas.append(row_dict)
        
        save_to_json(schemas, "table_schemas.json")
        
        # Get row counts
        print("\nGetting row counts...")
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
            print(f"  {table}: {count:,} rows")
        
        save_to_json(counts, "row_counts.json")
        
        print("\n✅ Data download complete!")
        
    except pyodbc.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    os.chdir('..')  # Go back to project root
    
    # Create newSQL directory if it doesn't exist
    if not os.path.exists('newSQL'):
        os.makedirs('newSQL')
    
    main()
#!/usr/bin/env python3
"""
Extract data from SQL Server and populate EstimateDoc SQLite database
This script regenerates the document data from original sources
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from decimal import Decimal
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Database connection details from .env
SQL_SERVER = os.getenv('DB_SERVER', 'mosmar-cip.database.windows.net,1433')
SQL_DATABASE = os.getenv('DB_NAME', 'Mosmar_CIP_Dev')
SQL_USERNAME = os.getenv('DB_USER', 'mosmaradmin')
SQL_PASSWORD = os.getenv('DB_PASSWORD')

# SQLite database path
SQLITE_DB_PATH = 'src/database/estimatedoc.db'

class DataExtractor:
    """Extract data from SQL Server and Excel sources"""
    
    def __init__(self):
        self.sql_conn = None
        self.sqlite_conn = None
        self.documents_data = []
        
    def connect_sql_server(self):
        """Connect to SQL Server"""
        if not SQL_PASSWORD:
            print("⚠️  DB_PASSWORD not found in .env file")
            print("Skipping SQL Server connection - will use cached JSON files if available")
            return None
            
        try:
            connection_string = (
                f'DRIVER={{ODBC Driver 18 for SQL Server}};'
                f'SERVER={SQL_SERVER};'
                f'DATABASE={SQL_DATABASE};'
                f'UID={SQL_USERNAME};'
                f'PWD={SQL_PASSWORD};'
                f'TrustServerCertificate=yes;'
            )
            self.sql_conn = pyodbc.connect(connection_string)
            print(f"✅ Connected to SQL Server: {SQL_SERVER}/{SQL_DATABASE}")
            return self.sql_conn
        except Exception as e:
            print(f"⚠️  Could not connect to SQL Server: {e}")
            print("Will try to use cached JSON files instead")
            return None
    
    def extract_from_sql_server(self):
        """Extract data directly from SQL Server"""
        if not self.sql_conn:
            return self.load_from_json_cache()
        
        cursor = self.sql_conn.cursor()
        
        # Get field analysis data
        print("📊 Extracting field analysis from SQL Server...")
        query = """
        SELECT
            DOC.documentid,
            DOC.filename,
            DOC.clienttitle,
            DOC.clientdescription,
            F.fieldcode,
            F.fieldresult,
            CASE
                WHEN F.fieldcode LIKE '%UDSCH%' THEN 'Search'
                WHEN F.fieldcode LIKE '%~%' THEN 'Reflection'
                WHEN F.fieldcode LIKE '%IF%' THEN 'If'
                WHEN F.fieldcode LIKE '%DOCVARIABLE "#%' THEN 'Built In Script'
                WHEN F.fieldcode LIKE '%$$%' THEN 'Extended'
                WHEN F.fieldcode LIKE '%SCR%' THEN 'Scripted'
                WHEN F.fieldcode LIKE '%[_]%' THEN 'Unbound'
                ELSE 'Precedent Script'
            END AS field_category
        FROM
            documents DOC
        LEFT JOIN
            DocumentFields DF ON DOC.DocumentID = DF.DocumentID
        LEFT JOIN
            fields F ON F.fieldid = DF.FieldID
        ORDER BY DOC.documentid;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Process SQL data into document structure
        documents_dict = {}
        for row in rows:
            doc_id = row[0]
            if doc_id not in documents_dict:
                documents_dict[doc_id] = {
                    'sql_doc_id': doc_id,
                    'sql_filename': row[1] or f"{doc_id}.dot",
                    'client_title': row[2] or f"Document_{doc_id}",
                    'client_description': row[3] or "Legal document template",
                    'fields': {
                        'If': [],
                        'Precedent Script': [],
                        'Reflection': [],
                        'Search': [],
                        'Unbound': [],
                        'Built In Script': [],
                        'Extended': [],
                        'Scripted': []
                    }
                }
            
            if row[4]:  # If fieldcode exists
                field_category = row[6]
                documents_dict[doc_id]['fields'][field_category].append({
                    'code': row[4],
                    'result': row[5]
                })
        
        print(f"✅ Extracted {len(documents_dict)} documents from SQL Server")
        return list(documents_dict.values())
    
    def load_from_json_cache(self):
        """Load data from cached JSON files"""
        print("📂 Loading from cached JSON files...")
        
        json_path = Path("../newSQL/field_analysis.json")
        if not json_path.exists():
            print("❌ No cached JSON files found. Please run SQL extraction first.")
            return []
        
        with open(json_path, 'r') as f:
            field_data = json.load(f)
        
        # Process JSON data into document structure
        documents_dict = {}
        for row in field_data:
            doc_id = row.get('documentid')
            if doc_id not in documents_dict:
                documents_dict[doc_id] = {
                    'sql_doc_id': doc_id,
                    'sql_filename': row.get('filename', f"{doc_id}.dot"),
                    'client_title': row.get('clienttitle', f"Document_{doc_id}"),
                    'client_description': row.get('clientdescription', "Legal document template"),
                    'fields': {
                        'If': [],
                        'Precedent Script': [],
                        'Reflection': [],
                        'Search': [],
                        'Unbound': [],
                        'Built In Script': [],
                        'Extended': [],
                        'Scripted': []
                    }
                }
            
            if row.get('fieldcode'):
                field_category = row.get('field_category', 'Precedent Script')
                documents_dict[doc_id]['fields'][field_category].append({
                    'code': row['fieldcode'],
                    'result': row.get('fieldresult')
                })
        
        print(f"✅ Loaded {len(documents_dict)} documents from JSON cache")
        return list(documents_dict.values())
    
    def enhance_with_excel_data(self, sql_documents):
        """Enhance SQL data with Excel analysis"""
        excel_path = Path("../The336/The336_Field_Analysis_Enhanced.xlsx")
        
        if not excel_path.exists():
            print("⚠️  Excel file not found, using SQL data only")
            return sql_documents
        
        print("📊 Enhancing with Excel analysis data...")
        df = pd.read_excel(excel_path)
        
        # Create lookup dictionary from Excel data
        excel_lookup = {}
        for _, row in df.iterrows():
            sql_id = row['SQLDocID'] if pd.notna(row['SQLDocID']) else None
            if sql_id:
                excel_lookup[int(sql_id)] = row
        
        # Enhance each document
        enhanced_documents = []
        for doc in sql_documents:
            doc_id = doc['sql_doc_id']
            
            # Get Excel row if exists
            excel_row = excel_lookup.get(doc_id, {})
            
            # Count fields by type
            field_counts = {
                'if': len(doc['fields'].get('If', [])),
                'precedent_script': len(doc['fields'].get('Precedent Script', [])),
                'reflection': len(doc['fields'].get('Reflection', [])),
                'search': len(doc['fields'].get('Search', [])),
                'unbound': len(doc['fields'].get('Unbound', [])),
                'built_in_script': len(doc['fields'].get('Built In Script', [])),
                'extended': len(doc['fields'].get('Extended', [])),
                'scripted': len(doc['fields'].get('Scripted', []))
            }
            
            # Calculate total fields
            total_fields = sum(field_counts.values())
            
            # Calculate effort based on field types
            if_minutes = field_counts['if'] * 7
            scripted_minutes = (field_counts['precedent_script'] + 
                               field_counts['scripted'] + 
                               field_counts['built_in_script']) * 15
            tag_minutes = (field_counts['reflection'] + 
                          field_counts['extended'] + 
                          field_counts['unbound']) * 1
            search_minutes = field_counts['search'] * 1
            
            total_minutes = if_minutes + scripted_minutes + tag_minutes + search_minutes
            calculated_hours = total_minutes / 60.0
            
            # Determine complexity (using Excel data if available)
            if isinstance(excel_row, pd.Series) and 'Assigned_Complexity' in excel_row:
                complexity_level = excel_row['Assigned_Complexity']
            else:
                # Default complexity rules
                total_scripts = (field_counts['precedent_script'] + 
                               field_counts['built_in_script'] + 
                               field_counts['scripted'])
                
                if total_fields < 10 and total_scripts <= 2:
                    complexity_level = 'Simple'
                elif total_fields >= 10 and total_fields <= 50 and total_scripts < 10:
                    complexity_level = 'Moderate'
                else:
                    complexity_level = 'Complex'
            
            # Apply complexity multiplier
            if complexity_level == 'Complex':
                multiplier = 0.5587
            elif complexity_level == 'Moderate':
                multiplier = 4.89
            else:  # Simple
                multiplier = 6.08
            
            optimized_hours = calculated_hours * multiplier
            
            # Build enhanced document
            enhanced_doc = {
                'id': doc_id,
                'name': doc['client_title'],
                'description': doc['client_description'],
                'sql_filename': doc['sql_filename'],
                'sql_doc_id': doc_id,
                'field_counts': field_counts,
                'total_fields': total_fields,
                'complexity_level': complexity_level,
                'effort_calculated': calculated_hours,
                'effort_optimized': optimized_hours,
                'effort_savings': abs(calculated_hours - optimized_hours),
                'evidence_source': 'SQL',
                'match_strategy': excel_row.get('MatchStrategy', 'Direct') if isinstance(excel_row, pd.Series) else 'Direct',
                'analysis_date': datetime.now().date().isoformat()
            }
            
            enhanced_documents.append(enhanced_doc)
        
        print(f"✅ Enhanced {len(enhanced_documents)} documents")
        return enhanced_documents
    
    def initialize_sqlite_db(self):
        """Initialize SQLite database"""
        print("🗄️  Initializing SQLite database...")
        
        # Create database directory if needed
        db_dir = Path(SQLITE_DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        
        # Read and execute schema
        schema_path = Path("src/database/schema.sql")
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            self.sqlite_conn.executescript(schema_sql)
            print("✅ Database schema created")
        else:
            print("❌ Schema file not found")
            return False
        
        return True
    
    def populate_sqlite_db(self, documents):
        """Populate SQLite database with document data"""
        print(f"💾 Populating database with {len(documents)} documents...")
        
        cursor = self.sqlite_conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Clear existing data
            cursor.execute("DELETE FROM documents")
            
            # Insert documents
            for doc in documents:
                # Prepare field counts with proper column names
                field_data = {
                    'if_count': doc['field_counts'].get('if', 0),
                    'precedent_script_count': doc['field_counts'].get('precedent_script', 0),
                    'reflection_count': doc['field_counts'].get('reflection', 0),
                    'search_count': doc['field_counts'].get('search', 0),
                    'unbound_count': doc['field_counts'].get('unbound', 0),
                    'built_in_script_count': doc['field_counts'].get('built_in_script', 0),
                    'extended_count': doc['field_counts'].get('extended', 0),
                    'scripted_count': doc['field_counts'].get('scripted', 0)
                }
                
                cursor.execute("""
                    INSERT INTO documents (
                        id, name, description, sql_filename, sql_doc_id,
                        if_count, precedent_script_count, reflection_count,
                        search_count, unbound_count, built_in_script_count,
                        extended_count, scripted_count,
                        total_all_fields, complexity_level,
                        effort_calculated, effort_optimized, effort_savings,
                        evidence_source, match_strategy, analysis_date,
                        data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc['id'],
                    doc['name'],
                    doc['description'],
                    doc['sql_filename'],
                    doc['sql_doc_id'],
                    field_data['if_count'],
                    field_data['precedent_script_count'],
                    field_data['reflection_count'],
                    field_data['search_count'],
                    field_data['unbound_count'],
                    field_data['built_in_script_count'],
                    field_data['extended_count'],
                    field_data['scripted_count'],
                    doc['total_fields'],
                    doc['complexity_level'],
                    doc['effort_calculated'],
                    doc['effort_optimized'],
                    doc['effort_savings'],
                    doc['evidence_source'],
                    doc['match_strategy'],
                    doc['analysis_date'],
                    'SQL'
                ))
            
            # Record sync history
            cursor.execute("""
                INSERT INTO sync_history (
                    sync_type, source_file, records_processed,
                    status, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'full_extraction',
                'SQL Server + Excel',
                len(documents),
                'success',
                datetime.now(),
                datetime.now()
            ))
            
            # Commit transaction
            self.sqlite_conn.commit()
            print(f"✅ Successfully populated database with {len(documents)} documents")
            
            # Show statistics
            cursor.execute("SELECT * FROM document_statistics")
            stats = cursor.fetchall()
            print("\n📊 Document Statistics:")
            print("Complexity | Count | Calc Hours | Opt Hours | Savings")
            print("-" * 55)
            for stat in stats:
                print(f"{stat[0]:10} | {stat[1]:5} | {stat[2]:10.2f} | {stat[3]:9.2f} | {stat[4]:7.2f}")
            
            # Calculate totals
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_docs,
                    SUM(effort_calculated) as total_calc,
                    SUM(effort_optimized) as total_opt
                FROM documents
            """)
            totals = cursor.fetchone()
            print("-" * 55)
            print(f"{'TOTAL':10} | {totals[0]:5} | {totals[1]:10.2f} | {totals[2]:9.2f} | {totals[1]-totals[2]:7.2f}")
            
        except Exception as e:
            # Rollback on error
            self.sqlite_conn.rollback()
            print(f"❌ Error populating database: {e}")
            raise
    
    def run(self):
        """Main extraction and population process"""
        print("\n🚀 Starting EstimateDoc Data Extraction and Database Population")
        print("=" * 60)
        
        try:
            # Step 1: Connect to SQL Server
            self.connect_sql_server()
            
            # Step 2: Extract data
            sql_documents = self.extract_from_sql_server()
            
            if not sql_documents:
                print("❌ No documents extracted")
                return False
            
            # Step 3: Enhance with Excel data
            enhanced_documents = self.enhance_with_excel_data(sql_documents)
            
            # Step 4: Initialize SQLite database
            if not self.initialize_sqlite_db():
                return False
            
            # Step 5: Populate database
            self.populate_sqlite_db(enhanced_documents)
            
            print("\n✅ Data extraction and database population complete!")
            print(f"📂 Database created at: {SQLITE_DB_PATH}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during extraction: {e}")
            return False
        
        finally:
            # Clean up connections
            if self.sql_conn:
                self.sql_conn.close()
                print("🔌 SQL Server connection closed")
            if self.sqlite_conn:
                self.sqlite_conn.close()
                print("🔌 SQLite connection closed")

def main():
    """Main entry point"""
    extractor = DataExtractor()
    success = extractor.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
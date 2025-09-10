#!/usr/bin/env python3
"""
Complete data extraction for EstimateDoc
Incorporates all data sources: SQL, ClientRequirements, Manifest XML, and Precedent XMLs
Based on the multi-strategy mapping approach documented in MAPPING_APPROACH_DOCUMENTATION.md
"""

import xml.etree.ElementTree as ET
import json
import pandas as pd
import re
import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CompleteDataExtractor:
    """Complete extraction including all mapping strategies"""
    
    def __init__(self):
        self.client_requirements = None
        self.sql_documents = None
        self.field_analysis = None
        self.manifest_data = {}
        self.precedent_xmls = {}
        self.mapping_results = []
        self.sqlite_conn = None
        
    def load_all_data_sources(self):
        """Load all data sources required for complete mapping"""
        print("\n📂 Loading All Data Sources...")
        
        # 1. Client Requirements
        client_path = Path("../ImportantData/ClientRequirements.xlsx")
        if not client_path.exists():
            client_path = Path("../ImportantData/ClientRequirements.csv")
            if client_path.exists():
                self.client_requirements = pd.read_csv(client_path)
            else:
                print("⚠️  ClientRequirements file not found")
                self.client_requirements = pd.DataFrame()
        else:
            self.client_requirements = pd.read_excel(client_path)
        print(f"✓ Client Requirements: {len(self.client_requirements)} items")
        
        # 2. SQL Documents
        sql_docs_path = Path("../newSQL/documents.json")
        if sql_docs_path.exists():
            with open(sql_docs_path, 'r') as f:
                self.sql_documents = json.load(f)
            print(f"✓ SQL Documents: {len(self.sql_documents)} items")
        else:
            print("⚠️  SQL documents not found")
            self.sql_documents = []
        
        # 3. Field Analysis
        field_analysis_path = Path("../newSQL/field_analysis.json")
        if field_analysis_path.exists():
            with open(field_analysis_path, 'r') as f:
                self.field_analysis = json.load(f)
            print(f"✓ Field Analysis: {len(self.field_analysis)} records")
        else:
            print("⚠️  Field analysis not found")
            self.field_analysis = []
        
        # Build lookups
        self.build_sql_lookups()
        self.build_field_analysis_by_doc()
    
    def build_sql_lookups(self):
        """Build various lookups for SQL documents"""
        self.sql_by_numeric = {}
        self.sql_by_filename = {}
        self.sql_by_basename = {}
        
        for doc in self.sql_documents:
            filename = doc.get('Filename', '')
            if filename:
                self.sql_by_filename[filename.lower()] = doc
                basename = filename.replace('.dot', '').replace('.docx', '').lower()
                self.sql_by_basename[basename] = doc
                
                # Extract pure numeric
                if re.match(r'^\d+$', basename):
                    self.sql_by_numeric[basename] = doc
        
        print(f"✓ SQL lookups: {len(self.sql_by_numeric)} numeric, {len(self.sql_by_basename)} basenames")
    
    def build_field_analysis_by_doc(self):
        """Build field analysis grouped by document"""
        self.field_by_doc = defaultdict(lambda: defaultdict(int))
        for fa in self.field_analysis:
            doc_id = fa.get('documentid')
            category = fa.get('field_category')
            if doc_id and category:
                self.field_by_doc[doc_id][category] += 1
    
    def parse_main_manifest(self):
        """Parse the main ExportSandI.Manifest.xml"""
        print("\n📄 Parsing Main Manifest...")
        
        manifest_path = Path("../ImportantData/ExportSandI.Manifest.xml")
        if not manifest_path.exists():
            print("⚠️  Main manifest not found")
            return
        
        try:
            tree = ET.parse(manifest_path)
            root = tree.getroot()
            
            self.manifest_by_name = {}
            self.manifest_by_code = {}
            
            for item in root.findall('.//Items[@Type="Precedents"]'):
                code = item.get('Code')
                name = item.get('Name')
                description = item.get('Description', '')
                
                if code and name:
                    # Clean name
                    clean_name = re.sub(r'\s*\(del:\d+\)', '', name).strip()
                    
                    # Extract title from description
                    desc_lines = description.split('\n')
                    prec_title = None
                    if len(desc_lines) >= 3:
                        prec_title = desc_lines[2].strip()
                    
                    info = {
                        'code': code,
                        'name': clean_name,
                        'prec_title': prec_title,
                        'description': description
                    }
                    
                    self.manifest_by_name[clean_name.lower()] = info
                    self.manifest_by_code[code] = info
                    
                    # Also index by prec_title if available
                    if prec_title:
                        self.manifest_by_name[prec_title.lower()] = info
            
            print(f"✓ Main manifest: {len(self.manifest_by_code)} codes, {len(self.manifest_by_name)} names")
        
        except Exception as e:
            print(f"❌ Error parsing main manifest: {e}")
    
    def parse_precedent_xmls(self):
        """Parse individual precedent XML files"""
        print("\n📁 Parsing Precedent XML Files...")
        
        precedents_path = Path("../ImportantData/ExportSandI/Precedents")
        if not precedents_path.exists():
            print("⚠️  Precedents folder not found")
            return
        
        precedent_folders = list(precedents_path.iterdir())
        print(f"Found {len(precedent_folders)} precedent folders")
        
        self.prec_by_folder = {}
        self.prec_by_title = {}
        self.prec_by_numeric = {}
        
        success_count = 0
        fail_count = 0
        
        for folder in precedent_folders:
            if folder.is_dir():
                manifest_file = folder / 'manifest.xml'
                if manifest_file.exists():
                    try:
                        tree = ET.parse(manifest_file)
                        root = tree.getroot()
                        
                        prec_data = {
                            'folder': folder.name,
                            'prec_title': root.findtext('.//PrecTitle', '').strip(),
                            'prec_path': root.findtext('.//PrecPath', '').strip(),
                            'prec_code': root.findtext('.//PrecCode', '').strip(),
                            'prec_preview': root.findtext('.//PrecPreview', '').strip()[:500]
                        }
                        
                        # Extract numeric from PrecPath
                        if prec_data['prec_path']:
                            path_match = re.search(r'(\d+)\.dot', prec_data['prec_path'])
                            if path_match:
                                numeric = path_match.group(1)
                                prec_data['sql_numeric'] = numeric
                                self.prec_by_numeric[numeric] = prec_data
                        
                        self.prec_by_folder[folder.name] = prec_data
                        
                        if prec_data['prec_title']:
                            self.prec_by_title[prec_data['prec_title'].lower()] = prec_data
                        
                        success_count += 1
                    
                    except Exception as e:
                        fail_count += 1
        
        print(f"✓ Successfully parsed {success_count} XML files, {fail_count} failed")
        print(f"✓ Mapped {len(self.prec_by_numeric)} numeric references")
    
    def perform_complete_mapping(self):
        """Perform the complete multi-strategy mapping"""
        print("\n🔗 Performing Complete Multi-Strategy Mapping...")
        
        mapping_results = []
        
        for _, row in self.client_requirements.iterrows():
            current_title = str(row.get('Current Title', '')).strip()
            if not current_title:
                continue
            
            result = {
                'client_name': current_title,
                'description': row.get('Description', ''),
                'client_complexity': row.get('Complexity', ''),
                'mapping_strategy': None,
                'sql_doc_id': None,
                'sql_filename': None,
                'manifest_code': None,
                'field_counts': {},
                'total_fields': 0,
                'effort_hours': 0
            }
            
            # Try mapping strategies in order
            
            # Strategy 1: Direct SQL Match
            if current_title.lower() in self.sql_by_basename:
                sql_doc = self.sql_by_basename[current_title.lower()]
                result['mapping_strategy'] = 'Direct SQL'
                result['sql_doc_id'] = sql_doc.get('DocumentID')
                result['sql_filename'] = sql_doc.get('Filename')
                result['field_counts'] = self.field_by_doc.get(result['sql_doc_id'], {})
            
            # Strategy 2: PrecPath Extraction
            elif current_title.lower() in self.prec_by_title:
                prec_data = self.prec_by_title[current_title.lower()]
                if 'sql_numeric' in prec_data and prec_data['sql_numeric'] in self.sql_by_numeric:
                    sql_doc = self.sql_by_numeric[prec_data['sql_numeric']]
                    result['mapping_strategy'] = 'PrecPath'
                    result['sql_doc_id'] = sql_doc.get('DocumentID')
                    result['sql_filename'] = sql_doc.get('Filename')
                    result['field_counts'] = self.field_by_doc.get(result['sql_doc_id'], {})
            
            # Strategy 3: Manifest Code Mapping
            elif current_title.lower() in self.manifest_by_name:
                manifest_info = self.manifest_by_name[current_title.lower()]
                result['manifest_code'] = manifest_info['code']
                
                # Try to find SQL doc by code
                if manifest_info['code'] in self.sql_by_numeric:
                    sql_doc = self.sql_by_numeric[manifest_info['code']]
                    result['mapping_strategy'] = 'Manifest Code'
                    result['sql_doc_id'] = sql_doc.get('DocumentID')
                    result['sql_filename'] = sql_doc.get('Filename')
                    result['field_counts'] = self.field_by_doc.get(result['sql_doc_id'], {})
                else:
                    result['mapping_strategy'] = 'Manifest Only'
            
            else:
                result['mapping_strategy'] = 'Unmatched'
            
            # Calculate totals and effort if we have field data
            if result['field_counts']:
                result['total_fields'] = sum(result['field_counts'].values())
                result['effort_hours'] = self.calculate_effort(result['field_counts'])
            
            mapping_results.append(result)
        
        self.mapping_results = mapping_results
        
        # Print summary
        strategies = defaultdict(int)
        for r in mapping_results:
            if r['mapping_strategy']:
                strategies[r['mapping_strategy']] += 1
        
        print(f"\n📊 Mapping Summary:")
        for strategy, count in sorted(strategies.items(), key=lambda x: (x[0] or '')):
            percentage = (count / len(mapping_results)) * 100 if mapping_results else 0
            print(f"  {strategy}: {count} ({percentage:.1f}%)")
        
        total_with_sql = sum(1 for r in mapping_results if r['sql_doc_id'])
        print(f"\n✓ Total mapped to SQL: {total_with_sql}/{len(mapping_results)} ({(total_with_sql/len(mapping_results)*100):.1f}%)")
    
    def calculate_effort(self, field_counts):
        """Calculate effort hours based on field counts"""
        # Effort map in minutes per field type
        effort_map = {
            'Reflection': 1,
            'Extended': 1,
            'Unbound': 1,
            'Search': 1,
            'If': 7,
            'Built In Script': 15,
            'Scripted': 15,
            'Precedent Script': 15
        }
        
        total_minutes = 0
        for category, count in field_counts.items():
            minutes_per_field = effort_map.get(category, 5)
            total_minutes += count * minutes_per_field
        
        return total_minutes / 60.0
    
    def populate_complete_database(self):
        """Populate SQLite database with complete mapping data"""
        print("\n💾 Populating Complete Database...")
        
        # Create database directory if needed
        db_path = Path("src/database/estimatedoc_complete.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to SQLite
        self.sqlite_conn = sqlite3.connect(db_path)
        cursor = self.sqlite_conn.cursor()
        
        # Create enhanced schema
        cursor.executescript("""
        DROP TABLE IF EXISTS documents_complete;
        DROP TABLE IF EXISTS mapping_history;
        
        CREATE TABLE documents_complete (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            description TEXT,
            client_complexity TEXT,
            mapping_strategy TEXT,
            manifest_code TEXT,
            sql_doc_id INTEGER,
            sql_filename TEXT,
            
            -- Field counts
            if_count INTEGER DEFAULT 0,
            precedent_script_count INTEGER DEFAULT 0,
            reflection_count INTEGER DEFAULT 0,
            search_count INTEGER DEFAULT 0,
            unbound_count INTEGER DEFAULT 0,
            built_in_script_count INTEGER DEFAULT 0,
            extended_count INTEGER DEFAULT 0,
            scripted_count INTEGER DEFAULT 0,
            
            -- Totals
            total_fields INTEGER DEFAULT 0,
            effort_hours REAL DEFAULT 0,
            
            -- Complexity (calculated)
            complexity_level TEXT,
            
            -- Metadata
            data_source TEXT DEFAULT 'Complete',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE mapping_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_clients INTEGER,
            total_mapped INTEGER,
            direct_sql INTEGER,
            precpath INTEGER,
            manifest_code INTEGER,
            manifest_only INTEGER,
            unmatched INTEGER
        );
        
        CREATE INDEX idx_client_name ON documents_complete(client_name);
        CREATE INDEX idx_mapping_strategy ON documents_complete(mapping_strategy);
        CREATE INDEX idx_complexity ON documents_complete(complexity_level);
        """)
        
        # Insert mapping results
        for result in self.mapping_results:
            # Determine complexity based on total fields and effort
            if result['total_fields'] < 10:
                complexity = 'Simple'
            elif result['total_fields'] < 50:
                complexity = 'Moderate'
            else:
                complexity = 'Complex'
            
            cursor.execute("""
                INSERT INTO documents_complete (
                    client_name, description, client_complexity,
                    mapping_strategy, manifest_code, sql_doc_id, sql_filename,
                    if_count, precedent_script_count, reflection_count,
                    search_count, unbound_count, built_in_script_count,
                    extended_count, scripted_count,
                    total_fields, effort_hours, complexity_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['client_name'],
                result['description'],
                result['client_complexity'],
                result['mapping_strategy'],
                result['manifest_code'],
                result['sql_doc_id'],
                result['sql_filename'],
                result['field_counts'].get('If', 0),
                result['field_counts'].get('Precedent Script', 0),
                result['field_counts'].get('Reflection', 0),
                result['field_counts'].get('Search', 0),
                result['field_counts'].get('Unbound', 0),
                result['field_counts'].get('Built In Script', 0),
                result['field_counts'].get('Extended', 0),
                result['field_counts'].get('Scripted', 0),
                result['total_fields'],
                result['effort_hours'],
                complexity
            ))
        
        # Record mapping history
        strategies = defaultdict(int)
        for r in self.mapping_results:
            strategies[r['mapping_strategy']] += 1
        
        cursor.execute("""
            INSERT INTO mapping_history (
                total_clients, total_mapped,
                direct_sql, precpath, manifest_code,
                manifest_only, unmatched
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            len(self.mapping_results),
            sum(1 for r in self.mapping_results if r['sql_doc_id']),
            strategies.get('Direct SQL', 0),
            strategies.get('PrecPath', 0),
            strategies.get('Manifest Code', 0),
            strategies.get('Manifest Only', 0),
            strategies.get('Unmatched', 0)
        ))
        
        self.sqlite_conn.commit()
        print(f"✅ Populated database with {len(self.mapping_results)} documents")
        
        # Show summary
        cursor.execute("""
            SELECT 
                complexity_level,
                COUNT(*) as count,
                SUM(effort_hours) as total_hours
            FROM documents_complete
            WHERE sql_doc_id IS NOT NULL
            GROUP BY complexity_level
        """)
        
        print("\n📊 Database Summary (Mapped Documents):")
        print("Complexity | Count | Total Hours")
        print("-" * 35)
        total_count = 0
        total_hours = 0
        for row in cursor.fetchall():
            print(f"{row[0]:10} | {row[1]:5} | {row[2]:10.2f}")
            total_count += row[1]
            total_hours += row[2]
        print("-" * 35)
        print(f"{'TOTAL':10} | {total_count:5} | {total_hours:10.2f}")
        
        self.sqlite_conn.close()
        print(f"\n✅ Complete database created at: {db_path}")
    
    def run(self):
        """Execute the complete extraction and mapping process"""
        print("\n" + "=" * 60)
        print("🚀 COMPLETE DATA EXTRACTION WITH ALL MAPPING STRATEGIES")
        print("=" * 60)
        
        try:
            # Load all data sources
            self.load_all_data_sources()
            
            # Parse XML sources
            self.parse_main_manifest()
            self.parse_precedent_xmls()
            
            # Perform complete mapping
            self.perform_complete_mapping()
            
            # Populate database
            self.populate_complete_database()
            
            print("\n✨ Complete extraction finished successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main entry point"""
    extractor = CompleteDataExtractor()
    success = extractor.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
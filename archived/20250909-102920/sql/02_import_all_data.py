#!/usr/bin/env python3
"""
Complete data import script for EstimateDoc PostgreSQL database
Implements the matching guidance from Excel_to_Dataset_Matching_Guidance.md
"""

import json
import re
import xml.etree.ElementTree as ET
import zipfile
import base64
import os
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dotenv_file(path: Path):
    try:
        if path.exists():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
    except Exception:
        pass

# Load local .env if present at repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv_file(REPO_ROOT / '.env')

def get_db_config():
    # Prefer explicit Postgres keys first, then fall back to DB_* if provided for Postgres, else defaults
    host = os.getenv('Host') or os.getenv('DB_HOST') or 'localhost'
    port = int(os.getenv('Port') or os.getenv('DB_PORT') or '5432')
    name = os.getenv('Database') or os.getenv('DB_NAME') or 'estimatedoc'
    user = os.getenv('User') or os.getenv('DB_USER') or 'estimatedoc_user'
    password = os.getenv('Password') or os.getenv('DB_PASSWORD') or 'estimatedoc_user'
    return {'host': host, 'port': port, 'database': name, 'user': user, 'password': password}

# Database configuration (from env)
DB_CONFIG = get_db_config()

# File paths
BASE_PATH = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData')
# Allow overriding Excel file path via env var ESTIMATEDOC_EXCEL_FILE
EXCEL_FILE = Path(os.getenv('ESTIMATEDOC_EXCEL_FILE') or (BASE_PATH / 'Super Template Requirements_received 23072025.xlsx'))
JSON_PATH = BASE_PATH / 'SQLExport'
MANIFEST_XML = BASE_PATH / 'ExportSandI.Manifest.xml'
EXPORT_SANDI_PATH = BASE_PATH / 'ExportSandI'

class EstimateDocImporter:
    def __init__(self):
        """Initialize the importer with database connection"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self.precedents_cache = {}
        self.documents_cache = {}
        self.mode_map = {}  # code -> id
        self.doc_mode_cache = {}  # document_id -> preferred mode_id (or None)
        
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
            
    def log_import(self, import_type, file_name, processed, imported, failed, error=None, status='completed'):
        """Log import operation to audit table"""
        self.cursor.execute("""
            INSERT INTO import_audit 
            (import_type, file_name, records_processed, records_imported, 
             records_failed, error_details, completed_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (import_type, file_name, processed, imported, failed, error, datetime.now(), status))
        self.conn.commit()
        
    # ========================================================================
    # STEP 1: Import Documents
    # ========================================================================
    
    def import_documents(self):
        """Import documents from dbo_Documents.json"""
        logger.info("Importing documents...")
        json_file = JSON_PATH / 'dbo_Documents.json'
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        documents = data.get('data', [])
        processed = 0
        imported = 0
        
        for doc in documents:
            try:
                self.cursor.execute("""
                    INSERT INTO documents (document_id, filename)
                    VALUES (%s, %s)
                    ON CONFLICT (document_id) DO UPDATE
                    SET filename = EXCLUDED.filename
                """, (doc['DocumentID'], doc['Filename']))
                imported += 1
            except Exception as e:
                logger.error(f"Error importing document {doc['DocumentID']}: {e}")
            processed += 1
            
        self.conn.commit()
        self.log_import('documents', str(json_file), processed, imported, processed - imported)
        logger.info(f"Documents imported: {imported}/{processed}")
        
        # Cache documents for matching
        self.cursor.execute("SELECT document_id, basename FROM documents")
        self.documents_cache = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        # Classify document channels from filename
        self._ensure_modes_seeded()
        self._classify_document_channels()
        
    # ========================================================================
    # STEP 2: Import Fields
    # ========================================================================
    
    def import_fields(self):
        """Import fields from dbo_Fields.json"""
        logger.info("Importing fields...")
        json_file = JSON_PATH / 'dbo_Fields.json'
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        fields = data.get('data', [])
        processed = 0
        imported = 0
        
        batch = []
        for field in fields:
            batch.append((
                field['FieldID'],
                field['FieldCode'],
                field.get('FieldResult')
            ))
            processed += 1
            
            if len(batch) >= 1000:
                self._insert_fields_batch(batch)
                imported += len(batch)
                batch = []
                
        if batch:
            self._insert_fields_batch(batch)
            imported += len(batch)
            
        self.conn.commit()
        self.log_import('fields', str(json_file), processed, imported, processed - imported)
        logger.info(f"Fields imported: {imported}/{processed}")
        
    def _insert_fields_batch(self, batch):
        """Insert a batch of fields"""
        execute_batch(self.cursor, """
            INSERT INTO fields (field_id, field_code, field_result)
            VALUES (%s, %s, %s)
            ON CONFLICT (field_id) DO UPDATE
            SET field_code = EXCLUDED.field_code,
                field_result = EXCLUDED.field_result
        """, batch)
        
    # ========================================================================
    # STEP 3: Import Document-Field Relationships
    # ========================================================================
    
    def import_document_fields(self):
        """Import document-field relationships from dbo_DocumentFields.json"""
        logger.info("Importing document-field relationships...")
        json_file = JSON_PATH / 'dbo_DocumentFields.json'
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        relationships = data.get('data', [])
        processed = 0
        imported = 0
        
        batch = []
        for rel in relationships:
            batch.append((
                rel['DocumentID'],
                rel['FieldID'],
                rel.get('Count', 1)
            ))
            processed += 1
            
            if len(batch) >= 1000:
                self._insert_doc_fields_batch(batch)
                imported += len(batch)
                batch = []
                
        if batch:
            self._insert_doc_fields_batch(batch)
            imported += len(batch)
            
        self.conn.commit()
        self.log_import('document_fields', str(json_file), processed, imported, processed - imported)
        logger.info(f"Document-field relationships imported: {imported}/{processed}")
        
    def _insert_doc_fields_batch(self, batch):
        """Insert a batch of document-field relationships"""
        execute_batch(self.cursor, """
            INSERT INTO document_fields (document_id, field_id, count)
            VALUES (%s, %s, %s)
            ON CONFLICT (document_id, field_id) DO UPDATE
            SET count = EXCLUDED.count
        """, batch)
        
    # ========================================================================
    # STEP 4: Import Precedents from Manifest
    # ========================================================================
    
    def import_precedents(self):
        """Import precedents from ExportSandI.Manifest.xml"""
        logger.info("Importing precedents from manifest...")
        
        tree = ET.parse(MANIFEST_XML)
        root = tree.getroot()
        
        processed = 0
        imported = 0
        
        for item in root.findall('.//Items'):
            try:
                if item.get('Type') == 'Precedents':
                    precedent_id = int(item.get('Code', 0))
                    if precedent_id > 0:
                        self.cursor.execute("""
                            INSERT INTO precedents 
                            (precedent_id, code, name, description, type, active, parent_id, image_index)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (precedent_id) DO UPDATE
                            SET name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                type = EXCLUDED.type
                        """, (
                            precedent_id,
                            item.get('Code', ''),
                            item.get('Name', ''),
                            item.get('Description', ''),
                            item.get('Type', ''),
                            item.get('Active', 'True') == 'True',
                            int(item.get('ParentID', 0)),
                            int(item.get('ImageIndex', 0))
                        ))
                        imported += 1
                processed += 1
            except Exception as e:
                logger.error(f"Error importing precedent: {e}")
                
        self.conn.commit()
        self.log_import('precedents', str(MANIFEST_XML), processed, imported, processed - imported)
        logger.info(f"Precedents imported: {imported}/{processed}")
        
        # Cache precedents for matching
        self.cursor.execute("SELECT precedent_id, normalized_code, normalized_name FROM precedents")
        for row in self.cursor.fetchall():
            self.precedents_cache[row[1]] = row[0]  # code -> id
            self.precedents_cache[row[2]] = row[0]  # name -> id
            
    # ========================================================================
    # STEP 5: Import Excel Templates
    # ========================================================================
    
    def import_excel_templates(self):
        """Import templates from Excel file"""
        logger.info("Importing Excel templates...")
        
        # Extract Excel data using zipfile (xlsx is a zip)
        excel_data = self._extract_excel_data()
        
        processed = 0
        imported = 0
        
        for i, row in enumerate(excel_data[1:], 1):  # Skip header
            if len(row) >= 3:
                # Extract identifiers
                template_code = row[0] if len(row) > 0 else ''
                description = row[1] if len(row) > 1 else ''
                stated_complexity = row[2] if len(row) > 2 else ''
                
                # Extract patterns
                excel_code = self._extract_code(template_code + ' ' + description)
                excel_name = self._extract_sup_name(template_code + ' ' + description)
                excel_filename = self._extract_filename(template_code + ' ' + description)
                
                # Value mining from description
                val_digits, val_sup = self._extract_values_from_text(description)
                
                # Determine candidate filename
                candidate = self._get_candidate_filename(
                    excel_filename, excel_code, excel_name, val_digits, val_sup
                )
                
                try:
                    self.cursor.execute("""
                        INSERT INTO excel_templates 
                        (sheet_name, row_number, template_code, description, stated_complexity,
                         excel_code, excel_name, excel_filename, val_digits, val_sup, candidate_filename)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING row_id
                    """, (
                        'Sheet1', i, template_code, description, stated_complexity,
                        excel_code, excel_name, excel_filename, val_digits, val_sup, candidate
                    ))
                    row_id = self.cursor.fetchone()[0]
                    imported += 1

                    # Classify channel(s) from title + description
                    modes = self._classify_text_channel(f"{template_code} {description}")
                    for mode_code in modes:
                        mode_id = self._get_mode_id(mode_code)
                        if mode_id:
                            self.cursor.execute(
                                """
                                INSERT INTO excel_template_channels (excel_row_id, mode_id, source)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (excel_row_id, mode_id) DO NOTHING
                                """,
                                (row_id, mode_id, 'excel_description')
                            )
                except Exception as e:
                    logger.error(f"Error importing Excel row {i}: {e}")
                processed += 1
                
        self.conn.commit()
        self.log_import('excel_templates', str(EXCEL_FILE), processed, imported, processed - imported)
        logger.info(f"Excel templates imported: {imported}/{processed}")
        
    def _extract_excel_data(self):
        """Extract data from Excel file"""
        z = zipfile.ZipFile(EXCEL_FILE)
        
        # Get shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.parse(z.open('xl/sharedStrings.xml'))
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            for si in tree.findall('.//s:si', ns):
                t = si.find('.//s:t', ns)
                shared_strings.append(t.text if t is not None and t.text else '')
        
        # Read first sheet
        sheet_data = []
        tree = ET.parse(z.open('xl/worksheets/sheet1.xml'))
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        for row in tree.findall('.//s:row', ns):
            row_data = []
            for cell in row.findall('.//s:c', ns):
                v = cell.find('.//s:v', ns)
                if v is not None:
                    cell_type = cell.get('t', 'n')
                    if cell_type == 's':  # shared string
                        idx = int(v.text)
                        row_data.append(shared_strings[idx] if idx < len(shared_strings) else '')
                    else:
                        row_data.append(v.text)
                else:
                    row_data.append('')
            if row_data and any(row_data):
                sheet_data.append(row_data)
                
        return sheet_data
        
    def _extract_code(self, text):
        """Extract numeric code from text"""
        match = re.search(r'\b(\d{3,})\b', text)
        return match.group(1) if match else None
        
    def _extract_sup_name(self, text):
        """Extract Sup name from text"""
        match = re.search(r'\b(sup[0-9a-z]+)\b', text, re.IGNORECASE)
        return match.group(1).lower() if match else None
        
    def _extract_filename(self, text):
        """Extract filename from text"""
        match = re.search(r'([A-Za-z0-9_\-]+)\.(dot|docx?|xsl|xslt)', text, re.IGNORECASE)
        return match.group(0).lower() if match else None
        
    def _extract_values_from_text(self, text):
        """Extract value-mined digits and sup names from text"""
        # Look for bracketed numbers
        digits_match = re.search(r'\[(\d{3,})\]', text)
        val_digits = digits_match.group(1) if digits_match else None
        
        # Look for embedded sup names
        sup_match = re.search(r'\b(sup[0-9a-z]+)\b', text, re.IGNORECASE)
        val_sup = sup_match.group(1).lower() if sup_match else None
        
        return val_digits, val_sup
        
    def _get_candidate_filename(self, excel_filename, excel_code, excel_name, val_digits, val_sup):
        """Determine candidate filename for matching"""
        if excel_filename:
            return excel_filename
        elif excel_code:
            return f"{excel_code}.dot"
        elif excel_name:
            return f"{excel_name}.dot"
        elif val_digits:
            return f"{val_digits}.dot"
        elif val_sup:
            return f"{val_sup}.dot"
        return None
        
    # ========================================================================
    # STEP 6: Perform Template Matching
    # ========================================================================
    
    def perform_template_matching(self):
        """Match Excel templates to documents and precedents"""
        logger.info("Performing template matching...")
        
        # Get all Excel templates
        self.cursor.execute("""
            SELECT row_id, excel_code, excel_name, excel_filename, 
                   val_digits, val_sup, candidate_filename
            FROM excel_templates
        """)
        templates = self.cursor.fetchall()
        
        matched = 0
        unmatched = 0
        
        for template in templates:
            row_id, excel_code, excel_name, excel_filename, val_digits, val_sup, candidate = template
            
            match_result = self._match_template(
                row_id, excel_code, excel_name, excel_filename, 
                val_digits, val_sup, candidate
            )
            
            if match_result['document_id'] or match_result['precedent_id']:
                matched += 1
            else:
                unmatched += 1
                
        self.conn.commit()
        logger.info(f"Template matching complete: {matched} matched, {unmatched} unmatched")
        
    def _match_template(self, row_id, excel_code, excel_name, excel_filename, 
                       val_digits, val_sup, candidate):
        """Match a single template using the deterministic pipeline"""
        result = {
            'document_id': None,
            'precedent_id': None,
            'match_method': 'unmatched',
            'match_confidence': 'Low',
            'unmatched_reason': None
        }
        
        # 1. Try exact filename match
        if candidate and candidate in self.documents_cache:
            result['document_id'] = self.documents_cache[candidate]
            result['match_method'] = 'filename'
            result['match_confidence'] = 'High'
            
        # 2. Try code → manifest → filename → documents
        elif excel_code:
            code_filename = f"{excel_code}.dot"
            if code_filename in self.documents_cache:
                result['document_id'] = self.documents_cache[code_filename]
                result['match_method'] = 'code_manifest'
                result['match_confidence'] = 'High'
            # Also check precedents
            if excel_code in self.precedents_cache:
                result['precedent_id'] = self.precedents_cache[excel_code]
                
        # 3. Try sup-name → manifest → filename → documents
        elif excel_name:
            name_filename = f"{excel_name}.dot"
            if name_filename in self.documents_cache:
                result['document_id'] = self.documents_cache[name_filename]
                result['match_method'] = 'sup_manifest'
                result['match_confidence'] = 'Medium'
            # Also check precedents
            if excel_name in self.precedents_cache:
                result['precedent_id'] = self.precedents_cache[excel_name]
                
        # 4. Try value mining
        elif val_digits or val_sup:
            if val_digits:
                val_filename = f"{val_digits}.dot"
                if val_filename in self.documents_cache:
                    result['document_id'] = self.documents_cache[val_filename]
                    result['match_method'] = 'name_value'
                    result['match_confidence'] = 'Medium'
            if not result['document_id'] and val_sup:
                val_filename = f"{val_sup}.dot"
                if val_filename in self.documents_cache:
                    result['document_id'] = self.documents_cache[val_filename]
                    result['match_method'] = 'name_value'
                    result['match_confidence'] = 'Medium'
                    
        # 5. Check for ZIP-only evidence
        if not result['document_id'] and (excel_code or excel_name):
            # Check if precedent folder exists
            precedent_path = EXPORT_SANDI_PATH / 'Precedents'
            if excel_code and (precedent_path / excel_code).exists():
                result['match_method'] = 'zip_only'
                result['match_confidence'] = 'Low'
                result['zip_rel_path'] = f"ExportSandI/Precedents/{excel_code}/manifest.xml"
            elif excel_name and (precedent_path / excel_name).exists():
                result['match_method'] = 'zip_only'
                result['match_confidence'] = 'Low'
                result['zip_rel_path'] = f"ExportSandI/Precedents/{excel_name}/manifest.xml"
                
        # Determine unmatched reason
        if result['match_method'] == 'unmatched':
            if not (excel_code or excel_name or excel_filename):
                result['unmatched_reason'] = 'No identifier in Excel'
            elif excel_filename and excel_filename not in self.documents_cache:
                result['unmatched_reason'] = 'Excel filename not in Documents'
            elif excel_code and excel_code not in self.precedents_cache:
                result['unmatched_reason'] = 'Excel code not in Manifest'
            elif excel_name and excel_name not in self.precedents_cache:
                result['unmatched_reason'] = 'Excel name not in Manifest'
            else:
                result['unmatched_reason'] = 'Manifest matched but Documents missing'
                
        # Insert match result
        # Decide mode_id for match: prefer document channel, else excel row single mode, else null
        mode_id = None
        if result['document_id'] and result['document_id'] in self.doc_mode_cache:
            mode_id = self.doc_mode_cache[result['document_id']]
        if mode_id is None:
            modes = self._get_excel_row_modes(row_id)
            # pick single non-unknown if available
            non_unknown = [m for m in modes if m != 'unknown']
            pick = non_unknown[0] if len(non_unknown) == 1 else None
            if pick:
                mode_id = self._get_mode_id(pick)

        self.cursor.execute("""
            INSERT INTO template_matches 
            (excel_row_id, document_id, precedent_id, candidate_filename,
             match_method, match_confidence, unmatched_reason, zip_rel_path, mode_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (excel_row_id) DO UPDATE
            SET document_id = EXCLUDED.document_id,
                precedent_id = EXCLUDED.precedent_id,
                match_method = EXCLUDED.match_method,
                match_confidence = EXCLUDED.match_confidence,
                mode_id = COALESCE(EXCLUDED.mode_id, template_matches.mode_id)
        """, (
            row_id, result['document_id'], result['precedent_id'], candidate,
            result['match_method'], result['match_confidence'],
            result['unmatched_reason'], result.get('zip_rel_path'), mode_id
        ))
        
        return result
        
    # ========================================================================
    # STEP 7: Calculate Complexity Metrics
    # ========================================================================
    
    def calculate_complexity_metrics(self):
        """Calculate complexity metrics for all documents"""
        logger.info("Calculating complexity metrics...")
        
        self.cursor.execute("SELECT document_id FROM documents")
        documents = self.cursor.fetchall()
        
        processed = 0
        for (doc_id,) in documents:
            try:
                self.cursor.execute("SELECT calculate_document_complexity(%s)", (doc_id,))
                processed += 1
                
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{len(documents)} documents")
                    self.conn.commit()
            except Exception as e:
                logger.error(f"Error calculating complexity for document {doc_id}: {e}")
                
        self.conn.commit()
        logger.info(f"Complexity metrics calculated for {processed} documents")
        
    # ========================================================================
    # STEP 8: Import Scripts
    # ========================================================================
    
    def import_scripts(self):
        """Import scripts from manifest files"""
        logger.info("Importing scripts...")
        
        scripts_path = EXPORT_SANDI_PATH / 'Scripts'
        if not scripts_path.exists():
            logger.warning("Scripts directory not found")
            return
            
        processed = 0
        imported = 0
        
        for script_dir in scripts_path.iterdir():
            if script_dir.is_dir():
                manifest_file = script_dir / 'manifest.xml'
                if manifest_file.exists():
                    try:
                        self._import_script_manifest(manifest_file)
                        imported += 1
                    except Exception as e:
                        logger.error(f"Error importing script {script_dir.name}: {e}")
                    processed += 1
                    
        self.conn.commit()
        self.log_import('scripts', 'Scripts/*.xml', processed, imported, processed - imported)
        logger.info(f"Scripts imported: {imported}/{processed}")
        
    def _import_script_manifest(self, manifest_file):
        """Import a single script from its manifest"""
        tree = ET.parse(manifest_file)
        root = tree.getroot()
        
        # Find the SCRIPTS element
        script_elem = root.find('.//SCRIPTS')
        if script_elem is not None:
            code = script_elem.findtext('scrCode', '')
            script_type = script_elem.findtext('scrType', '')
            version = script_elem.findtext('scrVersion', '0')
            author = script_elem.findtext('scrAuthor', '')
            script_text_encoded = script_elem.findtext('scrText', '')
            
            # Decode script text if it's base64 encoded
            script_text = ''
            if script_text_encoded:
                try:
                    # The script text is XML-encoded, need to parse it
                    script_text = script_text_encoded  # Keep as is for now
                except:
                    script_text = script_text_encoded
                    
            self.cursor.execute("""
                INSERT INTO scripts (code, type, version, author, script_text)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE
                SET type = EXCLUDED.type,
                    version = EXCLUDED.version,
                    script_text = EXCLUDED.script_text
            """, (code, script_type, int(version) if version else 0, author, script_text))
            
    # ========================================================================
    # Main Import Process
    # ========================================================================
    
    def run_full_import(self):
        """Run the complete import process"""
        logger.info("Starting full data import...")
        start_time = datetime.now()
        
        try:
            # Seed modes
            self._ensure_modes_seeded()

            # Core data imports
            self.import_documents()
            self.import_fields()
            self.import_document_fields()
            
            # Precedent and template imports
            self.import_precedents()
            self.import_excel_templates()
            
            # Matching and analysis
            self.perform_template_matching()
            self.calculate_complexity_metrics()
            
            # Additional imports
            self.import_scripts()
            
            # Generate summary statistics
            self.generate_summary_stats()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Full import completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            self.conn.rollback()
            raise
            
    def generate_summary_stats(self):
        """Generate and display summary statistics"""
        logger.info("\n=== Import Summary Statistics ===")
        
        # Document stats
        self.cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = self.cursor.fetchone()[0]
        logger.info(f"Documents: {doc_count}")
        
        # Field stats
        self.cursor.execute("SELECT COUNT(*) FROM fields")
        field_count = self.cursor.fetchone()[0]
        logger.info(f"Fields: {field_count}")
        
        # Relationship stats
        self.cursor.execute("SELECT COUNT(*) FROM document_fields")
        rel_count = self.cursor.fetchone()[0]
        logger.info(f"Document-Field Relationships: {rel_count}")
        
        # Precedent stats
        self.cursor.execute("SELECT COUNT(*) FROM precedents")
        prec_count = self.cursor.fetchone()[0]
        logger.info(f"Precedents: {prec_count}")
        
        # Excel template stats
        self.cursor.execute("SELECT COUNT(*) FROM excel_templates")
        excel_count = self.cursor.fetchone()[0]
        logger.info(f"Excel Templates: {excel_count}")
        
        # Matching stats
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN document_id IS NOT NULL THEN 1 ELSE 0 END) as matched,
                SUM(CASE WHEN match_confidence = 'High' THEN 1 ELSE 0 END) as high_conf,
                SUM(CASE WHEN match_confidence = 'Medium' THEN 1 ELSE 0 END) as med_conf,
                SUM(CASE WHEN match_confidence = 'Low' THEN 1 ELSE 0 END) as low_conf
            FROM template_matches
        """)
        stats = self.cursor.fetchone()
        logger.info(f"Template Matches: {stats[1]}/{stats[0]} ({100*stats[1]/stats[0]:.1f}%)")
        logger.info(f"  High Confidence: {stats[2]}")
        logger.info(f"  Medium Confidence: {stats[3]}")
        logger.info(f"  Low Confidence: {stats[4]}")
        
        # Complexity distribution
        self.cursor.execute("""
            SELECT complexity_rating, COUNT(*)
            FROM document_complexity
            GROUP BY complexity_rating
            ORDER BY 
                CASE complexity_rating
                    WHEN 'Simple' THEN 1
                    WHEN 'Low' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'High' THEN 4
                    WHEN 'Very High' THEN 5
                END
        """)
        logger.info("Complexity Distribution:")
        for rating, count in self.cursor.fetchall():
            logger.info(f"  {rating}: {count}")

    # ===============================
    # Channel helpers
    # ===============================
    def _ensure_modes_seeded(self):
        self.cursor.execute("""
            INSERT INTO communication_modes (code, label)
            VALUES ('letter','Letter'),('email','Email'),('both','Both'),('unknown','Unknown')
            ON CONFLICT (code) DO NOTHING
        """)
        self.conn.commit()
        self.cursor.execute("SELECT id, code FROM communication_modes")
        self.mode_map = {code: mid for (mid, code) in self.cursor.fetchall()}

    def _get_mode_id(self, code: str):
        return self.mode_map.get(code)

    def _classify_text_channel(self, text: str):
        t = (text or '').lower()
        is_email = bool(re.search(r'\b(e-?mail|outlook|mail to|emailed)\b', t))
        is_letter = bool(re.search(r'\b(letter|ltr|postal|hardcopy|printed|post)\b', t))
        if is_email and is_letter:
            return ['both']
        if is_email:
            return ['email']
        if is_letter:
            return ['letter']
        return ['unknown']

    def _classify_document_channels(self):
        # derive from filename; update document_channels and cache preferred mode
        self.cursor.execute("SELECT document_id, filename FROM documents")
        docs = self.cursor.fetchall()
        for doc_id, filename in docs:
            modes = self._classify_text_channel(filename)
            # choose preferred for cache: non-unknown if possible
            preferred = None
            if modes[0] == 'both':
                preferred = self._get_mode_id('both')
            else:
                code = modes[0]
                preferred = self._get_mode_id(code)
            self.doc_mode_cache[doc_id] = preferred if preferred != self._get_mode_id('unknown') else None
            for mode_code in modes:
                mode_id = self._get_mode_id(mode_code)
                if mode_id:
                    self.cursor.execute(
                        """
                        INSERT INTO document_channels (document_id, mode_id, source)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (document_id, mode_id) DO NOTHING
                        """,
                        (doc_id, mode_id, 'filename')
                    )
        self.conn.commit()

    def _get_excel_row_modes(self, row_id: int):
        self.cursor.execute(
            """
            SELECT m.code
            FROM excel_template_channels etc
            JOIN communication_modes m ON m.id = etc.mode_id
            WHERE etc.excel_row_id = %s
            ORDER BY m.code
            """,
            (row_id,)
        )
        rows = [r[0] for r in self.cursor.fetchall()]
        return rows or []


if __name__ == "__main__":
    importer = EstimateDocImporter()
    importer.run_full_import()

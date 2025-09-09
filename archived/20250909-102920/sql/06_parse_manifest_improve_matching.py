#!/usr/bin/env python3
"""
Parse ExportSandI.Manifest.xml to dramatically improve template matching
This creates the bridge between Sup codes and numeric document IDs
"""

import xml.etree.ElementTree as ET
import psycopg2
import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estimatedoc',
    'user': 'estimatedoc_user',
    'password': 'estimatedoc_user'
}

class ManifestMatcher:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self.manifest_entries = []
        
    def parse_manifest(self, manifest_path):
        """Parse the ExportSandI.Manifest.xml file"""
        logger.info(f"Parsing manifest: {manifest_path}")
        
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        
        count = 0
        for item in root.findall('.//Items'):
            if item.get('Type') == 'Precedents':
                code = item.get('Code', '')
                name = item.get('Name', '')
                description = item.get('Description', '')
                
                # Clean up description - remove the metadata parts
                # Description format: "Precedent [code] \n\n actual_description \n\n Library: ..."
                desc_lines = description.split('\n')
                clean_desc = ''
                if len(desc_lines) >= 3:
                    # The actual description is usually the third line
                    clean_desc = desc_lines[2].strip()
                    # Remove any remaining escape sequences
                    clean_desc = clean_desc.replace('\r', '').replace('\xa0', ' ')
                
                if code and name:
                    self.manifest_entries.append({
                        'code': code,
                        'name': name,
                        'description': clean_desc,
                        'full_description': description,
                        'filename': f"{code}.dot"
                    })
                    count += 1
                    
        logger.info(f"Parsed {count} precedent entries from manifest")
        return count
        
    def populate_manifest_mappings(self):
        """Populate the manifest_mappings table"""
        logger.info("Populating manifest_mappings table...")
        
        # Clear existing mappings
        self.cursor.execute("TRUNCATE TABLE manifest_mappings")
        
        inserted = 0
        for entry in self.manifest_entries:
            try:
                self.cursor.execute("""
                    INSERT INTO manifest_mappings 
                    (manifest_code, manifest_name, manifest_description, document_filename)
                    VALUES (%s, %s, %s, %s)
                """, (
                    entry['code'],
                    entry['name'],
                    entry['description'],
                    entry['filename']
                ))
                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting manifest entry {entry['name']}: {e}")
                
        self.conn.commit()
        logger.info(f"Inserted {inserted} manifest mappings")
        return inserted
        
    def analyze_excel_patterns(self):
        """Analyze Excel template patterns to understand matching challenges"""
        logger.info("Analyzing Excel template patterns...")
        
        self.cursor.execute("""
            SELECT template_code, description 
            FROM excel_templates 
            WHERE template_code IS NOT NULL
            LIMIT 20
        """)
        
        excel_samples = self.cursor.fetchall()
        
        patterns = {
            'has_sup_code': 0,
            'has_numeric_in_desc': 0,
            'has_bracketed_code': 0,
            'exact_sup_match': 0
        }
        
        for code, desc in excel_samples:
            # Check for Sup pattern
            if re.match(r'^[Ss]up\d+[a-z]?', code):
                patterns['has_sup_code'] += 1
                
                # Check if this exact Sup exists in manifest
                if any(e['name'].lower() == code.lower() for e in self.manifest_entries):
                    patterns['exact_sup_match'] += 1
                    
            # Check for numeric codes in description
            if desc and re.search(r'\d{4,5}', desc):
                patterns['has_numeric_in_desc'] += 1
                
            # Check for bracketed codes
            if desc and re.search(r'\[\d{4,5}\]', desc):
                patterns['has_bracketed_code'] += 1
                
        logger.info(f"Pattern analysis: {patterns}")
        return patterns
        
    def perform_improved_matching(self):
        """Execute the improved matching algorithm"""
        logger.info("Performing improved template matching...")
        
        # Get current match statistics
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT et.row_id) as total_rows,
                COUNT(DISTINCT CASE WHEN tm.document_id IS NOT NULL THEN et.row_id END) as matched_before
            FROM excel_templates et
            LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
        """)
        before_stats = self.cursor.fetchone()
        logger.info(f"Before: {before_stats[1]}/{before_stats[0]} matched ({100*before_stats[1]/before_stats[0]:.1f}%)")
        
        # Strategy 1: Direct Sup name matching
        matched_by_sup = self._match_by_sup_name()
        
        # Strategy 2: Description similarity matching  
        matched_by_desc = self._match_by_description()
        
        # Strategy 3: Extract codes from descriptions
        matched_by_code = self._match_by_extracted_code()
        
        # Strategy 4: Fuzzy Sup matching (handles typos)
        matched_by_fuzzy = self._match_by_fuzzy_sup()
        
        total_improved = matched_by_sup + matched_by_desc + matched_by_code + matched_by_fuzzy
        
        # Get new match statistics
        self.cursor.execute("""
            SELECT COUNT(DISTINCT CASE WHEN document_id IS NOT NULL THEN excel_row_id END)
            FROM template_matches
        """)
        after_matched = self.cursor.fetchone()[0]
        
        logger.info(f"After: {after_matched}/{before_stats[0]} matched ({100*after_matched/before_stats[0]:.1f}%)")
        logger.info(f"Improvement: +{after_matched - before_stats[1]} matches")
        
        return {
            'before': before_stats[1],
            'after': after_matched,
            'total_rows': before_stats[0],
            'improved_by': after_matched - before_stats[1],
            'methods': {
                'sup_name': matched_by_sup,
                'description': matched_by_desc,
                'extracted_code': matched_by_code,
                'fuzzy_sup': matched_by_fuzzy
            }
        }
        
    def _match_by_sup_name(self):
        """Match by exact Sup name"""
        query = """
            INSERT INTO template_matches (excel_row_id, document_id, match_method, match_confidence, manifest_code, manifest_name)
            SELECT 
                et.row_id,
                d.document_id,
                'manifest_sup_exact',
                'High',
                mm.manifest_code,
                mm.manifest_name
            FROM excel_templates et
            JOIN manifest_mappings mm ON LOWER(et.template_code) = LOWER(mm.manifest_name)
            JOIN documents d ON mm.document_filename = d.basename
            ON CONFLICT (excel_row_id) DO UPDATE
            SET document_id = EXCLUDED.document_id,
                match_method = EXCLUDED.match_method,
                match_confidence = EXCLUDED.match_confidence,
                manifest_code = EXCLUDED.manifest_code,
                manifest_name = EXCLUDED.manifest_name
            WHERE template_matches.match_confidence < EXCLUDED.match_confidence
               OR template_matches.document_id IS NULL
        """
        self.cursor.execute(query)
        matched = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Matched {matched} by exact Sup name")
        return matched
        
    def _match_by_description(self):
        """Match by description similarity"""
        # First ensure pg_trgm extension is enabled
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        
        query = """
            WITH similarity_matches AS (
                SELECT 
                    et.row_id,
                    d.document_id,
                    mm.manifest_code,
                    mm.manifest_name,
                    similarity(et.description, mm.manifest_description) as sim_score
                FROM excel_templates et
                CROSS JOIN manifest_mappings mm
                JOIN documents d ON mm.document_filename = d.basename
                LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
                WHERE (tm.document_id IS NULL OR tm.match_confidence = 'Low')
                  AND et.description IS NOT NULL
                  AND mm.manifest_description IS NOT NULL
                  AND similarity(et.description, mm.manifest_description) > 0.4
            ),
            ranked_matches AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY row_id ORDER BY sim_score DESC) as rn
                FROM similarity_matches
            )
            INSERT INTO template_matches (excel_row_id, document_id, match_method, match_confidence, manifest_code, manifest_name)
            SELECT 
                row_id,
                document_id,
                'description_similarity',
                CASE 
                    WHEN sim_score > 0.7 THEN 'High'
                    WHEN sim_score > 0.5 THEN 'Medium'
                    ELSE 'Low'
                END,
                manifest_code,
                manifest_name
            FROM ranked_matches
            WHERE rn = 1
            ON CONFLICT (excel_row_id) DO UPDATE
            SET document_id = EXCLUDED.document_id,
                match_method = EXCLUDED.match_method,
                match_confidence = EXCLUDED.match_confidence,
                manifest_code = EXCLUDED.manifest_code,
                manifest_name = EXCLUDED.manifest_name
            WHERE template_matches.match_confidence < EXCLUDED.match_confidence
               OR template_matches.document_id IS NULL
        """
        self.cursor.execute(query)
        matched = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Matched {matched} by description similarity")
        return matched
        
    def _match_by_extracted_code(self):
        """Match by extracting numeric codes from descriptions"""
        query = """
            INSERT INTO template_matches (excel_row_id, document_id, match_method, match_confidence, manifest_code, manifest_name)
            SELECT DISTINCT
                et.row_id,
                d.document_id,
                'extracted_code',
                'Medium',
                mm.manifest_code,
                mm.manifest_name
            FROM excel_templates et
            JOIN manifest_mappings mm ON 
                mm.manifest_code = SUBSTRING(et.description FROM '\[?(\d{4,5})\]?')
                OR mm.manifest_code = SUBSTRING(et.template_code FROM '(\d{4,5})')
            JOIN documents d ON mm.document_filename = d.basename
            LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
            WHERE (tm.document_id IS NULL OR tm.match_confidence = 'Low')
            ON CONFLICT (excel_row_id) DO UPDATE
            SET document_id = EXCLUDED.document_id,
                match_method = EXCLUDED.match_method,
                match_confidence = EXCLUDED.match_confidence,
                manifest_code = EXCLUDED.manifest_code,
                manifest_name = EXCLUDED.manifest_name
            WHERE template_matches.match_confidence < EXCLUDED.match_confidence
               OR template_matches.document_id IS NULL
        """
        self.cursor.execute(query)
        matched = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Matched {matched} by extracted code")
        return matched
        
    def _match_by_fuzzy_sup(self):
        """Match by fuzzy Sup name matching (handles typos)"""
        # Ensure fuzzystrmatch extension for levenshtein
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
        
        query = """
            WITH fuzzy_candidates AS (
                SELECT 
                    et.row_id,
                    d.document_id,
                    mm.manifest_code,
                    mm.manifest_name,
                    levenshtein(LOWER(et.template_code), LOWER(mm.manifest_name)) as distance,
                    ROW_NUMBER() OVER (PARTITION BY et.row_id ORDER BY levenshtein(LOWER(et.template_code), LOWER(mm.manifest_name))) as rn
                FROM excel_templates et
                JOIN manifest_mappings mm ON 
                    levenshtein(LOWER(et.template_code), LOWER(mm.manifest_name)) <= 2
                    AND LENGTH(et.template_code) > 3
                JOIN documents d ON mm.document_filename = d.basename
                LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
                WHERE (tm.document_id IS NULL OR tm.match_confidence = 'Low')
                  AND (et.template_code ILIKE 'sup%')
            )
            INSERT INTO template_matches (excel_row_id, document_id, match_method, match_confidence, manifest_code, manifest_name)
            SELECT 
                row_id,
                document_id,
                'fuzzy_sup',
                'Medium',
                manifest_code,
                manifest_name
            FROM fuzzy_candidates
            WHERE rn = 1
            ON CONFLICT (excel_row_id) DO UPDATE
            SET document_id = EXCLUDED.document_id,
                match_method = EXCLUDED.match_method,
                match_confidence = EXCLUDED.match_confidence,
                manifest_code = EXCLUDED.manifest_code,
                manifest_name = EXCLUDED.manifest_name
            WHERE template_matches.match_confidence < EXCLUDED.match_confidence
               OR template_matches.document_id IS NULL
        """
        self.cursor.execute(query)
        matched = self.cursor.rowcount
        self.conn.commit()
        logger.info(f"  Matched {matched} by fuzzy Sup name")
        return matched
        
    def generate_match_report(self):
        """Generate a detailed matching report"""
        logger.info("\n" + "="*80)
        logger.info("MANIFEST-BASED MATCHING IMPROVEMENT REPORT")
        logger.info("="*80)
        
        # Overall statistics
        self.cursor.execute("""
            SELECT 
                COUNT(DISTINCT et.row_id) as total_rows,
                COUNT(DISTINCT CASE WHEN tm.document_id IS NOT NULL THEN et.row_id END) as matched_rows,
                COUNT(DISTINCT CASE WHEN tm.match_method = 'manifest_sup_exact' THEN et.row_id END) as sup_exact,
                COUNT(DISTINCT CASE WHEN tm.match_method = 'description_similarity' THEN et.row_id END) as desc_sim,
                COUNT(DISTINCT CASE WHEN tm.match_method = 'extracted_code' THEN et.row_id END) as extracted,
                COUNT(DISTINCT CASE WHEN tm.match_method = 'fuzzy_sup' THEN et.row_id END) as fuzzy
            FROM excel_templates et
            LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
        """)
        
        stats = self.cursor.fetchone()
        match_rate = 100 * stats[1] / stats[0] if stats[0] > 0 else 0
        
        logger.info(f"\n📊 MATCHING STATISTICS")
        logger.info(f"  Total Excel Templates: {stats[0]}")
        logger.info(f"  Matched Templates: {stats[1]} ({match_rate:.1f}%)")
        logger.info(f"\n  Matching Methods:")
        logger.info(f"    Exact Sup Name: {stats[2]}")
        logger.info(f"    Description Similarity: {stats[3]}")
        logger.info(f"    Extracted Code: {stats[4]}")
        logger.info(f"    Fuzzy Sup Match: {stats[5]}")
        
        # Sample successful matches
        logger.info(f"\n✅ SAMPLE SUCCESSFUL MATCHES")
        self.cursor.execute("""
            SELECT 
                et.template_code,
                tm.manifest_name,
                tm.manifest_code,
                tm.match_method,
                tm.match_confidence
            FROM excel_templates et
            JOIN template_matches tm ON et.row_id = tm.excel_row_id
            WHERE tm.document_id IS NOT NULL
            ORDER BY tm.match_confidence DESC, et.template_code
            LIMIT 10
        """)
        
        for row in self.cursor.fetchall():
            logger.info(f"  {row[0]:<15} → {row[1]:<15} ({row[2]:<6}) via {row[3]:<20} [{row[4]}]")
            
        # Remaining unmatched
        logger.info(f"\n❌ UNMATCHED TEMPLATES ANALYSIS")
        self.cursor.execute("""
            SELECT 
                COUNT(*) as unmatched_count,
                COUNT(DISTINCT CASE WHEN template_code ILIKE 'sup%' THEN row_id END) as unmatched_sup,
                COUNT(DISTINCT CASE WHEN template_code NOT ILIKE 'sup%' THEN row_id END) as unmatched_other
            FROM excel_templates et
            LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
            WHERE tm.document_id IS NULL
        """)
        
        unmatched = self.cursor.fetchone()
        logger.info(f"  Total Unmatched: {unmatched[0]}")
        logger.info(f"    Sup codes: {unmatched[1]}")
        logger.info(f"    Other codes: {unmatched[2]}")
        
    def run_full_improvement(self, manifest_path):
        """Run the complete improvement process"""
        # Parse manifest
        self.parse_manifest(manifest_path)
        
        # Populate mappings
        self.populate_manifest_mappings()
        
        # Analyze patterns
        self.analyze_excel_patterns()
        
        # Perform improved matching
        results = self.perform_improved_matching()
        
        # Generate report
        self.generate_match_report()
        
        return results


if __name__ == "__main__":
    manifest_path = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ExportSandI.Manifest.xml'
    
    matcher = ManifestMatcher()
    results = matcher.run_full_improvement(manifest_path)
    
    print(f"\n🎯 FINAL RESULT: Match rate improved from {results['before']}/{results['total_rows']} to {results['after']}/{results['total_rows']}")
    print(f"   That's {100*results['before']/results['total_rows']:.1f}% → {100*results['after']/results['total_rows']:.1f}%!")
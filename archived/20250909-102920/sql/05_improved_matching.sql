-- ============================================================================
-- IMPROVED MATCHING USING ExportSandI.Manifest.xml
-- This dramatically improves our match rate by using the manifest as a bridge
-- ============================================================================

-- Create a mapping table from the manifest
CREATE TABLE IF NOT EXISTS manifest_mappings (
    mapping_id SERIAL PRIMARY KEY,
    manifest_code VARCHAR(50),      -- The numeric code (e.g., "17553")
    manifest_name VARCHAR(100),      -- The Sup name (e.g., "Sup021c")
    manifest_description TEXT,       -- Full description text
    document_filename VARCHAR(255),  -- Expected filename (code + .dot)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast lookups
CREATE INDEX idx_manifest_code ON manifest_mappings(manifest_code);
CREATE INDEX idx_manifest_name ON manifest_mappings(LOWER(manifest_name));
CREATE INDEX idx_manifest_filename ON manifest_mappings(document_filename);

-- ============================================================================
-- IMPROVED MATCHING FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION improved_template_matching()
RETURNS TABLE (
    excel_row_id INTEGER,
    excel_template_code VARCHAR,
    excel_description TEXT,
    matched_via VARCHAR,
    document_id INTEGER,
    precedent_code VARCHAR,
    precedent_name VARCHAR,
    confidence_level VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- Step 1: Direct Sup name matches via manifest
    sup_matches AS (
        SELECT 
            et.row_id,
            et.template_code,
            et.description,
            'manifest_sup_name' as match_method,
            d.document_id,
            mm.manifest_code,
            mm.manifest_name,
            'High' as confidence
        FROM excel_templates et
        JOIN manifest_mappings mm ON LOWER(et.template_code) = LOWER(mm.manifest_name)
        LEFT JOIN documents d ON mm.document_filename = d.basename
        WHERE et.template_code LIKE 'sup%' OR et.template_code LIKE 'Sup%'
    ),
    
    -- Step 2: Description similarity matches
    description_matches AS (
        SELECT 
            et.row_id,
            et.template_code,
            et.description,
            'description_similarity' as match_method,
            d.document_id,
            mm.manifest_code,
            mm.manifest_name,
            CASE 
                WHEN similarity(et.description, mm.manifest_description) > 0.7 THEN 'High'
                WHEN similarity(et.description, mm.manifest_description) > 0.5 THEN 'Medium'
                ELSE 'Low'
            END as confidence
        FROM excel_templates et
        CROSS JOIN manifest_mappings mm
        LEFT JOIN documents d ON mm.document_filename = d.basename
        WHERE et.row_id NOT IN (SELECT row_id FROM sup_matches)
          AND similarity(et.description, mm.manifest_description) > 0.3
    ),
    
    -- Step 3: Code extraction from description
    code_extraction_matches AS (
        SELECT 
            et.row_id,
            et.template_code,
            et.description,
            'extracted_code' as match_method,
            d.document_id,
            mm.manifest_code,
            mm.manifest_name,
            'Medium' as confidence
        FROM excel_templates et
        JOIN manifest_mappings mm ON 
            -- Extract numeric codes from description like "[17553]" or "17553"
            mm.manifest_code = SUBSTRING(et.description FROM '\[?(\d{4,5})\]?')
        LEFT JOIN documents d ON mm.document_filename = d.basename
        WHERE et.row_id NOT IN (
            SELECT row_id FROM sup_matches 
            UNION SELECT row_id FROM description_matches
        )
    ),
    
    -- Step 4: Fuzzy Sup name matches
    fuzzy_sup_matches AS (
        SELECT 
            et.row_id,
            et.template_code,
            et.description,
            'fuzzy_sup_match' as match_method,
            d.document_id,
            mm.manifest_code,
            mm.manifest_name,
            'Medium' as confidence
        FROM excel_templates et
        JOIN manifest_mappings mm ON 
            -- Fuzzy match on Sup names (handles typos, case differences)
            levenshtein(LOWER(et.template_code), LOWER(mm.manifest_name)) <= 2
        LEFT JOIN documents d ON mm.document_filename = d.basename
        WHERE et.row_id NOT IN (
            SELECT row_id FROM sup_matches 
            UNION SELECT row_id FROM description_matches
            UNION SELECT row_id FROM code_extraction_matches
        )
        AND (et.template_code LIKE 'sup%' OR et.template_code LIKE 'Sup%')
    )
    
    -- Combine all matches
    SELECT * FROM sup_matches
    UNION ALL
    SELECT * FROM description_matches
    UNION ALL  
    SELECT * FROM code_extraction_matches
    UNION ALL
    SELECT * FROM fuzzy_sup_matches
    ORDER BY row_id, confidence DESC;
    
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- POPULATE MANIFEST MAPPINGS FROM XML
-- ============================================================================

-- This would be populated by parsing the ExportSandI.Manifest.xml
-- Example entries based on the manifest:
/*
INSERT INTO manifest_mappings (manifest_code, manifest_name, manifest_description, document_filename) VALUES
('17553', 'Sup021c', 'Letter to client advising – not proceeding with IP claim due to offsets', '17553.dot'),
('17554', 'Sup021d', 'Letter to client advising – loss of contact', '17554.dot'),
('17555', 'Sup021e', 'Letter to client advising – client returned to work/working', '17555.dot'),
('14778', 'Sup008', 'Letter to client confirming instructions to place matter on hold', '14778.dot'),
('9097', 'Sup005', 'Letter to Employer requesting information with attached questionnaire', '9097.dot'),
-- ... etc for all manifest entries
*/

-- ============================================================================
-- ANALYSIS VIEW: Show improvement in match rate
-- ============================================================================

CREATE OR REPLACE VIEW v_matching_improvement_analysis AS
WITH 
original_matches AS (
    SELECT COUNT(DISTINCT excel_row_id) as matched_count
    FROM template_matches
    WHERE document_id IS NOT NULL
),
improved_matches AS (
    SELECT COUNT(DISTINCT excel_row_id) as matched_count
    FROM improved_template_matching()
    WHERE document_id IS NOT NULL
),
total_rows AS (
    SELECT COUNT(*) as total_count FROM excel_templates
)
SELECT 
    t.total_count as total_excel_rows,
    o.matched_count as original_matched,
    i.matched_count as improved_matched,
    ROUND(100.0 * o.matched_count / t.total_count, 1) as original_match_rate,
    ROUND(100.0 * i.matched_count / t.total_count, 1) as improved_match_rate,
    i.matched_count - o.matched_count as additional_matches,
    ROUND(100.0 * (i.matched_count - o.matched_count) / NULLIF(o.matched_count, 0), 1) as improvement_percentage
FROM total_rows t, original_matches o, improved_matches i;

-- ============================================================================
-- UPDATE TEMPLATE MATCHES WITH IMPROVED ALGORITHM
-- ============================================================================

CREATE OR REPLACE FUNCTION update_matches_with_manifest()
RETURNS VOID AS $$
DECLARE
    v_match RECORD;
    v_updated INTEGER := 0;
BEGIN
    -- Clear existing poor matches
    DELETE FROM template_matches WHERE match_confidence = 'Low' AND document_id IS NULL;
    
    -- Process improved matches
    FOR v_match IN SELECT * FROM improved_template_matching()
    LOOP
        -- Update or insert match
        INSERT INTO template_matches (
            excel_row_id,
            document_id,
            precedent_id,
            match_method,
            match_confidence,
            manifest_code,
            manifest_name
        ) VALUES (
            v_match.excel_row_id,
            v_match.document_id,
            -- Try to find precedent by code
            (SELECT precedent_id FROM precedents WHERE code = v_match.precedent_code LIMIT 1),
            v_match.matched_via,
            v_match.confidence_level,
            v_match.precedent_code,
            v_match.precedent_name
        )
        ON CONFLICT (excel_row_id) DO UPDATE SET
            document_id = EXCLUDED.document_id,
            precedent_id = EXCLUDED.precedent_id,
            match_method = EXCLUDED.match_method,
            match_confidence = EXCLUDED.match_confidence,
            manifest_code = EXCLUDED.manifest_code,
            manifest_name = EXCLUDED.manifest_name,
            updated_at = CURRENT_TIMESTAMP
        WHERE template_matches.match_confidence < EXCLUDED.match_confidence
           OR template_matches.document_id IS NULL;
           
        v_updated := v_updated + 1;
    END LOOP;
    
    RAISE NOTICE 'Updated % template matches using manifest data', v_updated;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- DIAGNOSTIC: Find why templates aren't matching
-- ============================================================================

CREATE OR REPLACE VIEW v_unmatched_diagnosis AS
SELECT 
    et.row_id,
    et.template_code,
    LEFT(et.description, 100) as description_preview,
    -- Check if we have a manifest entry with this Sup code
    EXISTS(SELECT 1 FROM manifest_mappings WHERE LOWER(manifest_name) = LOWER(et.template_code)) as has_manifest_sup,
    -- Check if we have a similar description
    (SELECT MAX(similarity(et.description, mm.manifest_description)) FROM manifest_mappings mm) as max_description_similarity,
    -- Check if description contains a code
    SUBSTRING(et.description FROM '\[?(\d{4,5})\]?') as extracted_code,
    -- Check if that code exists in manifest
    EXISTS(SELECT 1 FROM manifest_mappings WHERE manifest_code = SUBSTRING(et.description FROM '\[?(\d{4,5})\]?')) as code_in_manifest,
    -- Suggest the most likely match
    (SELECT manifest_name || ' (' || manifest_code || ')' 
     FROM manifest_mappings mm 
     ORDER BY similarity(et.description, mm.manifest_description) DESC 
     LIMIT 1) as suggested_match
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
WHERE tm.document_id IS NULL
   OR tm.match_confidence = 'Low'
ORDER BY et.row_id;
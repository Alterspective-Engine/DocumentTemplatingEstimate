-- EstimateDoc PostgreSQL Database Schema
-- Version: 1.0
-- Purpose: Complete schema for legal document complexity analysis and cost estimation

-- Create database (run as superuser)
-- CREATE DATABASE estimatedoc;
-- \c estimatedoc;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text matching

-- Drop existing schema if needed (careful in production!)
-- DROP SCHEMA IF EXISTS public CASCADE;
-- CREATE SCHEMA public;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- 1. Documents table (from dbo_Documents.json)
CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    basename VARCHAR(255) GENERATED ALWAYS AS (LOWER(REGEXP_REPLACE(filename, '^.*/', ''))) STORED,
    file_extension VARCHAR(10) GENERATED ALWAYS AS (LOWER(REGEXP_REPLACE(filename, '^.*\.', ''))) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_basename ON documents(basename);
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_extension ON documents(file_extension);

-- 2. Fields table (from dbo_Fields.json)
CREATE TABLE IF NOT EXISTS fields (
    field_id INTEGER PRIMARY KEY,
    field_code TEXT NOT NULL,
    field_result TEXT,
    field_type VARCHAR(50),
    -- Calculated columns for field analysis
    is_docvariable BOOLEAN GENERATED ALWAYS AS (field_code ILIKE '%DOCVARIABLE%') STORED,
    is_mergefield BOOLEAN GENERATED ALWAYS AS (field_code ILIKE '%MERGEFIELD%') STORED,
    has_if_statement BOOLEAN GENERATED ALWAYS AS (
        UPPER(field_code) LIKE 'IF %' OR field_code ILIKE '% IF %'
    ) STORED,
    has_nested_if BOOLEAN GENERATED ALWAYS AS (
        (LENGTH(field_code) - LENGTH(REPLACE(UPPER(field_code), 'IF', ''))) / 2 >= 2
    ) STORED,
    has_calculation BOOLEAN GENERATED ALWAYS AS (
        field_code LIKE '%+%' OR field_code LIKE '%-%' OR 
        field_code LIKE '%*%' OR field_code LIKE '%/%' OR
        field_code LIKE '%=%' OR field_code LIKE '%>%' OR field_code LIKE '%<%'
    ) STORED,
    has_user_input BOOLEAN GENERATED ALWAYS AS (
        field_code LIKE '%!%' OR field_code ILIKE '%select%'
    ) STORED,
    field_length INTEGER GENERATED ALWAYS AS (LENGTH(field_code)) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fields_type ON fields(field_type);
CREATE INDEX idx_fields_docvar ON fields(is_docvariable);
CREATE INDEX idx_fields_merge ON fields(is_mergefield);
CREATE INDEX idx_fields_if ON fields(has_if_statement);

-- 3. Document-Field relationships (from dbo_DocumentFields.json)
CREATE TABLE IF NOT EXISTS document_fields (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    field_id INTEGER NOT NULL REFERENCES fields(field_id) ON DELETE CASCADE,
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, field_id)
);

CREATE INDEX idx_doc_fields_doc ON document_fields(document_id);
CREATE INDEX idx_doc_fields_field ON document_fields(field_id);
CREATE INDEX idx_doc_fields_composite ON document_fields(document_id, field_id);

-- ============================================================================
-- PRECEDENT TABLES
-- ============================================================================

-- 4. Precedents table (from ExportSandI.Manifest.xml)
CREATE TABLE IF NOT EXISTS precedents (
    precedent_id INTEGER PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    type VARCHAR(50),
    library VARCHAR(100),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    minor_category VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER,
    image_index INTEGER,
    -- Normalized fields for matching
    normalized_name VARCHAR(255) GENERATED ALWAYS AS (LOWER(TRIM(name))) STORED,
    normalized_code VARCHAR(50) GENERATED ALWAYS AS (REGEXP_REPLACE(code, '[^0-9]', '', 'g')) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_precedents_code ON precedents(code);
CREATE INDEX idx_precedents_name ON precedents(name);
CREATE INDEX idx_precedents_norm_name ON precedents(normalized_name);
CREATE INDEX idx_precedents_norm_code ON precedents(normalized_code);
CREATE INDEX idx_precedents_category ON precedents(category, subcategory, minor_category);

-- ============================================================================
-- EXCEL TEMPLATE TABLES
-- ============================================================================

-- 5. Excel template requirements
CREATE TABLE IF NOT EXISTS excel_templates (
    row_id SERIAL PRIMARY KEY,
    sheet_name VARCHAR(100),
    row_number INTEGER,
    -- Original Excel columns
    template_code VARCHAR(50),
    description TEXT,
    stated_complexity VARCHAR(50),
    -- Extracted identifiers
    excel_code VARCHAR(50),      -- Extracted numeric code
    excel_name VARCHAR(100),     -- Extracted Sup name (normalized)
    excel_filename VARCHAR(255), -- Extracted filename
    val_digits VARCHAR(50),      -- Value-mined digits
    val_sup VARCHAR(100),        -- Value-mined Sup name
    candidate_filename VARCHAR(255), -- Chosen candidate for matching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_excel_code ON excel_templates(excel_code);
CREATE INDEX idx_excel_name ON excel_templates(excel_name);
CREATE INDEX idx_excel_filename ON excel_templates(excel_filename);
CREATE INDEX idx_excel_complexity ON excel_templates(stated_complexity);

-- 6. Template matching results (implements matching guidance)
CREATE TABLE IF NOT EXISTS template_matches (
    match_id SERIAL PRIMARY KEY,
    excel_row_id INTEGER NOT NULL REFERENCES excel_templates(row_id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(document_id) ON DELETE SET NULL,
    precedent_id INTEGER REFERENCES precedents(precedent_id) ON DELETE SET NULL,
    -- Matching details
    candidate_filename VARCHAR(255),
    manifest_code VARCHAR(50),
    manifest_name VARCHAR(255),
    match_method VARCHAR(50), -- filename/code_manifest/sup_manifest/name_value/zip_only/unmatched
    match_confidence VARCHAR(20), -- High/Medium/Low
    unmatched_reason VARCHAR(100),
    zip_rel_path VARCHAR(500),
    note_conflict VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT match_method_check CHECK (match_method IN (
        'filename', 'code_manifest', 'sup_manifest', 
        'name_value', 'zip_only', 'unmatched'
    )),
    CONSTRAINT confidence_check CHECK (match_confidence IN ('High', 'Medium', 'Low'))
);

CREATE INDEX idx_matches_excel ON template_matches(excel_row_id);
CREATE INDEX idx_matches_doc ON template_matches(document_id);
CREATE INDEX idx_matches_prec ON template_matches(precedent_id);
CREATE INDEX idx_matches_method ON template_matches(match_method);
CREATE INDEX idx_matches_confidence ON template_matches(match_confidence);

-- ============================================================================
-- COMPLEXITY ANALYSIS TABLES
-- ============================================================================

-- 7. Document complexity metrics (calculated)
CREATE TABLE IF NOT EXISTS document_complexity (
    complexity_id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE UNIQUE,
    -- Field counts
    total_fields INTEGER DEFAULT 0,
    unique_fields INTEGER DEFAULT 0,
    reusable_fields INTEGER DEFAULT 0,
    -- Field type counts
    docvariable_fields INTEGER DEFAULT 0,
    mergefield_fields INTEGER DEFAULT 0,
    if_statements INTEGER DEFAULT 0,
    nested_if_statements INTEGER DEFAULT 0,
    unbound_fields INTEGER DEFAULT 0,
    user_input_fields INTEGER DEFAULT 0,
    calculated_fields INTEGER DEFAULT 0,
    complex_fields INTEGER DEFAULT 0,
    -- Field statistics
    avg_field_length DECIMAL(10,2),
    max_field_length INTEGER,
    min_field_length INTEGER,
    -- Complexity scoring
    total_complexity_score INTEGER DEFAULT 0,
    avg_complexity_score DECIMAL(10,2),
    complexity_rating VARCHAR(20), -- Simple/Low/Medium/High/Very High
    -- Timestamps
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rating_check CHECK (complexity_rating IN (
        'Simple', 'Low', 'Medium', 'High', 'Very High'
    ))
);

CREATE INDEX idx_complexity_doc ON document_complexity(document_id);
CREATE INDEX idx_complexity_rating ON document_complexity(complexity_rating);
CREATE INDEX idx_complexity_score ON document_complexity(total_complexity_score);

-- ============================================================================
-- SCRIPT TABLES
-- ============================================================================

-- 8. Scripts table (from Scripts manifests)
CREATE TABLE IF NOT EXISTS scripts (
    script_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(50),
    version INTEGER,
    author VARCHAR(100),
    script_text TEXT, -- Decoded from base64
    script_blob BYTEA, -- Original binary if needed
    format INTEGER,
    created TIMESTAMP,
    created_by INTEGER,
    updated TIMESTAMP,
    updated_by INTEGER,
    rowguid UUID DEFAULT uuid_generate_v4(),
    flag INTEGER DEFAULT 0
);

CREATE INDEX idx_scripts_code ON scripts(code);
CREATE INDEX idx_scripts_type ON scripts(type);

-- 9. Precedent scripts relationship
CREATE TABLE IF NOT EXISTS precedent_scripts (
    id SERIAL PRIMARY KEY,
    precedent_id INTEGER NOT NULL REFERENCES precedents(precedent_id) ON DELETE CASCADE,
    script_code VARCHAR(50) NOT NULL,
    execution_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(precedent_id, script_code)
);

CREATE INDEX idx_prec_scripts_prec ON precedent_scripts(precedent_id);
CREATE INDEX idx_prec_scripts_code ON precedent_scripts(script_code);

-- ============================================================================
-- AUDIT AND TRACKING TABLES
-- ============================================================================

-- 10. Import audit log
CREATE TABLE IF NOT EXISTS import_audit (
    audit_id SERIAL PRIMARY KEY,
    import_type VARCHAR(50) NOT NULL, -- documents/fields/precedents/excel/scripts
    file_name VARCHAR(255),
    records_processed INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_details TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running', -- running/completed/failed
    CONSTRAINT status_check CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_audit_type ON import_audit(import_type);
CREATE INDEX idx_audit_status ON import_audit(status);
CREATE INDEX idx_audit_started ON import_audit(started_at);

-- ============================================================================
-- VIEWS AND MATERIALIZED VIEWS
-- ============================================================================

-- Template analytics view
CREATE OR REPLACE VIEW v_template_analytics AS
SELECT 
    et.row_id,
    et.sheet_name,
    et.row_number,
    et.template_code,
    et.description,
    et.stated_complexity,
    et.excel_code,
    et.excel_name,
    tm.document_id,
    d.filename,
    d.basename,
    tm.precedent_id,
    p.code as precedent_code,
    p.name as precedent_name,
    p.category as precedent_category,
    tm.match_method,
    tm.match_confidence,
    tm.unmatched_reason,
    dc.total_fields,
    dc.unique_fields,
    dc.reusable_fields,
    dc.if_statements,
    dc.unbound_fields,
    dc.user_input_fields,
    dc.calculated_fields,
    dc.total_complexity_score,
    dc.complexity_rating as calculated_complexity,
    CASE 
        WHEN et.stated_complexity IS NULL THEN 'No Rating'
        WHEN LOWER(et.stated_complexity) = LOWER(dc.complexity_rating) THEN 'Match'
        WHEN tm.document_id IS NULL THEN 'Unmatched'
        ELSE 'Mismatch'
    END as complexity_agreement
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
LEFT JOIN documents d ON tm.document_id = d.document_id
LEFT JOIN precedents p ON tm.precedent_id = p.precedent_id
LEFT JOIN document_complexity dc ON d.document_id = dc.document_id;

-- Coverage statistics view
CREATE OR REPLACE VIEW v_coverage_stats AS
SELECT 
    COUNT(DISTINCT et.row_id) as total_excel_rows,
    COUNT(DISTINCT CASE WHEN tm.document_id IS NOT NULL THEN et.row_id END) as matched_to_document,
    COUNT(DISTINCT CASE WHEN tm.precedent_id IS NOT NULL THEN et.row_id END) as matched_to_precedent,
    COUNT(DISTINCT CASE WHEN tm.match_confidence = 'High' THEN et.row_id END) as high_confidence_matches,
    COUNT(DISTINCT CASE WHEN tm.match_confidence = 'Medium' THEN et.row_id END) as medium_confidence_matches,
    COUNT(DISTINCT CASE WHEN tm.match_confidence = 'Low' THEN et.row_id END) as low_confidence_matches,
    COUNT(DISTINCT CASE WHEN tm.match_method = 'unmatched' THEN et.row_id END) as unmatched_rows,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN tm.document_id IS NOT NULL THEN et.row_id END) / 
          NULLIF(COUNT(DISTINCT et.row_id), 0), 2) as document_match_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN tm.precedent_id IS NOT NULL THEN et.row_id END) / 
          NULLIF(COUNT(DISTINCT et.row_id), 0), 2) as precedent_match_rate
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id;

-- Complexity distribution view
CREATE OR REPLACE VIEW v_complexity_distribution AS
SELECT 
    complexity_rating,
    COUNT(*) as document_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage,
    ROUND(AVG(total_fields), 1) as avg_fields,
    ROUND(AVG(total_complexity_score), 1) as avg_score,
    MIN(total_complexity_score) as min_score,
    MAX(total_complexity_score) as max_score
FROM document_complexity
GROUP BY complexity_rating
ORDER BY 
    CASE complexity_rating
        WHEN 'Simple' THEN 1
        WHEN 'Low' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'High' THEN 4
        WHEN 'Very High' THEN 5
    END;

-- Field usage statistics view
CREATE OR REPLACE VIEW v_field_usage_stats AS
SELECT 
    f.field_id,
    f.field_code,
    f.field_type,
    COUNT(DISTINCT df.document_id) as used_in_documents,
    SUM(df.count) as total_usage_count,
    f.is_docvariable,
    f.is_mergefield,
    f.has_if_statement,
    f.has_calculation,
    f.has_user_input,
    f.field_length
FROM fields f
LEFT JOIN document_fields df ON f.field_id = df.field_id
GROUP BY f.field_id, f.field_code, f.field_type, 
         f.is_docvariable, f.is_mergefield, f.has_if_statement,
         f.has_calculation, f.has_user_input, f.field_length
ORDER BY total_usage_count DESC;

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_excel_templates_updated_at BEFORE UPDATE ON excel_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_template_matches_updated_at BEFORE UPDATE ON template_matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_precedents_updated_at BEFORE UPDATE ON precedents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_complexity_updated_at BEFORE UPDATE ON document_complexity
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate document complexity
CREATE OR REPLACE FUNCTION calculate_document_complexity(p_document_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_total_fields INTEGER;
    v_unique_fields INTEGER;
    v_complexity_score INTEGER;
    v_rating VARCHAR(20);
BEGIN
    -- Calculate field counts and complexity metrics
    WITH field_stats AS (
        SELECT 
            COUNT(*) as total_fields,
            COUNT(DISTINCT f.field_id) as unique_fields,
            COUNT(DISTINCT CASE WHEN f.is_docvariable THEN f.field_id END) as docvar_count,
            COUNT(DISTINCT CASE WHEN f.is_mergefield THEN f.field_id END) as merge_count,
            COUNT(DISTINCT CASE WHEN f.has_if_statement THEN f.field_id END) as if_count,
            COUNT(DISTINCT CASE WHEN f.has_nested_if THEN f.field_id END) as nested_if_count,
            COUNT(DISTINCT CASE WHEN f.field_result IS NULL OR f.field_result = '' THEN f.field_id END) as unbound_count,
            COUNT(DISTINCT CASE WHEN f.has_user_input THEN f.field_id END) as user_input_count,
            COUNT(DISTINCT CASE WHEN f.has_calculation THEN f.field_id END) as calc_count,
            AVG(f.field_length) as avg_length,
            MAX(f.field_length) as max_length,
            MIN(f.field_length) as min_length
        FROM document_fields df
        JOIN fields f ON df.field_id = f.field_id
        WHERE df.document_id = p_document_id
    )
    INSERT INTO document_complexity (
        document_id, total_fields, unique_fields, docvariable_fields,
        mergefield_fields, if_statements, nested_if_statements,
        unbound_fields, user_input_fields, calculated_fields,
        avg_field_length, max_field_length, min_field_length
    )
    SELECT 
        p_document_id,
        total_fields,
        unique_fields,
        docvar_count,
        merge_count,
        if_count,
        nested_if_count,
        unbound_count,
        user_input_count,
        calc_count,
        avg_length,
        max_length,
        min_length
    FROM field_stats
    ON CONFLICT (document_id) DO UPDATE SET
        total_fields = EXCLUDED.total_fields,
        unique_fields = EXCLUDED.unique_fields,
        docvariable_fields = EXCLUDED.docvariable_fields,
        mergefield_fields = EXCLUDED.mergefield_fields,
        if_statements = EXCLUDED.if_statements,
        nested_if_statements = EXCLUDED.nested_if_statements,
        unbound_fields = EXCLUDED.unbound_fields,
        user_input_fields = EXCLUDED.user_input_fields,
        calculated_fields = EXCLUDED.calculated_fields,
        avg_field_length = EXCLUDED.avg_field_length,
        max_field_length = EXCLUDED.max_field_length,
        min_field_length = EXCLUDED.min_field_length,
        calculated_at = CURRENT_TIMESTAMP;
    
    -- Calculate complexity score
    UPDATE document_complexity
    SET 
        total_complexity_score = 
            (if_statements * 3) +
            (nested_if_statements * 2) +
            (user_input_fields * 2) +
            (calculated_fields * 2) +
            (docvariable_fields * 1) +
            (mergefield_fields * 1),
        complexity_rating = CASE
            WHEN total_complexity_score = 0 THEN 'Simple'
            WHEN total_complexity_score BETWEEN 1 AND 9 THEN 'Low'
            WHEN total_complexity_score BETWEEN 10 AND 29 THEN 'Medium'
            WHEN total_complexity_score BETWEEN 30 AND 49 THEN 'High'
            ELSE 'Very High'
        END
    WHERE document_id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA AND CONSTRAINTS
-- ============================================================================

-- Add any default data or additional constraints here

-- ============================================================================
-- PERMISSIONS (adjust as needed)
-- ============================================================================

-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional indexes for common query patterns
CREATE INDEX idx_complexity_score_range ON document_complexity(total_complexity_score);
CREATE INDEX idx_fields_composite ON fields(is_docvariable, is_mergefield, has_if_statement);
CREATE INDEX idx_excel_stated_complexity ON excel_templates(stated_complexity);
CREATE INDEX idx_precedents_active ON precedents(active) WHERE active = TRUE;

-- Full text search indexes
CREATE INDEX idx_excel_description_gin ON excel_templates USING gin(to_tsvector('english', description));
CREATE INDEX idx_precedents_description_gin ON precedents USING gin(to_tsvector('english', description));

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE documents IS 'Core document records from dbo_Documents.json';
COMMENT ON TABLE fields IS 'Field definitions and patterns from dbo_Fields.json';
COMMENT ON TABLE document_fields IS 'Many-to-many relationship between documents and fields';
COMMENT ON TABLE precedents IS 'Legal precedent templates from ExportSandI manifest';
COMMENT ON TABLE excel_templates IS 'Template requirements from Excel workbook';
COMMENT ON TABLE template_matches IS 'Matching results between Excel rows and documents/precedents';
COMMENT ON TABLE document_complexity IS 'Calculated complexity metrics for each document';
COMMENT ON TABLE scripts IS 'Automation scripts associated with precedents';
COMMENT ON TABLE precedent_scripts IS 'Links between precedents and their scripts';
COMMENT ON TABLE import_audit IS 'Audit trail for data import processes';

COMMENT ON COLUMN template_matches.match_method IS 'Method used for matching: filename/code_manifest/sup_manifest/name_value/zip_only/unmatched';
COMMENT ON COLUMN template_matches.match_confidence IS 'Confidence level of the match: High/Medium/Low';
COMMENT ON COLUMN document_complexity.complexity_rating IS 'Calculated complexity level: Simple/Low/Medium/High/Very High';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
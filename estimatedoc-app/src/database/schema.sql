-- EstimateDoc Database Schema
-- SQLite database for storing document analysis data

-- Drop existing tables if they exist
DROP TABLE IF EXISTS document_fields;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS sync_history;

-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    sql_filename TEXT,
    sql_doc_id INTEGER,
    client_title TEXT,
    client_description TEXT,
    
    -- Field counts
    if_count INTEGER DEFAULT 0,
    if_unique INTEGER DEFAULT 0,
    if_reusable INTEGER DEFAULT 0,
    if_reuse_rate TEXT DEFAULT '0.0%',
    
    precedent_script_count INTEGER DEFAULT 0,
    precedent_script_unique INTEGER DEFAULT 0,
    precedent_script_reusable INTEGER DEFAULT 0,
    precedent_script_reuse_rate TEXT DEFAULT '0.0%',
    
    reflection_count INTEGER DEFAULT 0,
    reflection_unique INTEGER DEFAULT 0,
    reflection_reusable INTEGER DEFAULT 0,
    reflection_reuse_rate TEXT DEFAULT '0.0%',
    
    search_count INTEGER DEFAULT 0,
    search_unique INTEGER DEFAULT 0,
    search_reusable INTEGER DEFAULT 0,
    search_reuse_rate TEXT DEFAULT '0.0%',
    
    unbound_count INTEGER DEFAULT 0,
    unbound_unique INTEGER DEFAULT 0,
    unbound_reusable INTEGER DEFAULT 0,
    unbound_reuse_rate TEXT DEFAULT '0.0%',
    
    built_in_script_count INTEGER DEFAULT 0,
    built_in_script_unique INTEGER DEFAULT 0,
    built_in_script_reusable INTEGER DEFAULT 0,
    built_in_script_reuse_rate TEXT DEFAULT '0.0%',
    
    extended_count INTEGER DEFAULT 0,
    extended_unique INTEGER DEFAULT 0,
    extended_reusable INTEGER DEFAULT 0,
    extended_reuse_rate TEXT DEFAULT '0.0%',
    
    scripted_count INTEGER DEFAULT 0,
    scripted_unique INTEGER DEFAULT 0,
    scripted_reusable INTEGER DEFAULT 0,
    scripted_reuse_rate TEXT DEFAULT '0.0%',
    
    -- Totals
    total_all_fields INTEGER DEFAULT 0,
    total_unique_fields INTEGER DEFAULT 0,
    total_reusable_fields INTEGER DEFAULT 0,
    overall_reuse_rate TEXT DEFAULT '0.0%',
    
    -- Complexity
    complexity_level TEXT CHECK(complexity_level IN ('Simple', 'Moderate', 'Complex')),
    complexity_reason TEXT,
    complexity_calculation JSON,
    
    -- Effort
    effort_calculated REAL DEFAULT 0,
    effort_optimized REAL DEFAULT 0,
    effort_savings REAL DEFAULT 0,
    effort_calculation JSON,
    
    -- Evidence
    evidence_source TEXT,
    evidence_details TEXT,
    evidence_query TEXT,
    evidence_confidence INTEGER,
    evidence_traceability JSON,
    
    -- Metadata
    match_strategy TEXT,
    excel_complexity TEXT,
    data_source TEXT DEFAULT 'SQL',
    analysis_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document fields detail table (for future expansion)
CREATE TABLE document_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN (
        'if', 'precedentScript', 'reflection', 'search', 
        'unbound', 'builtInScript', 'extended', 'scripted'
    )),
    field_code TEXT,
    field_result TEXT,
    field_category TEXT,
    is_unique BOOLEAN DEFAULT 0,
    is_reusable BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Sync history table to track data updates
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,
    source_file TEXT,
    records_processed INTEGER,
    status TEXT CHECK(status IN ('success', 'failed', 'partial')),
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_documents_complexity ON documents(complexity_level);
CREATE INDEX idx_documents_name ON documents(name);
CREATE INDEX idx_documents_total_fields ON documents(total_all_fields);
CREATE INDEX idx_document_fields_document_id ON document_fields(document_id);
CREATE INDEX idx_document_fields_type ON document_fields(field_type);
CREATE INDEX idx_sync_history_status ON sync_history(status);
CREATE INDEX idx_sync_history_created ON sync_history(created_at);

-- View for document statistics
CREATE VIEW document_statistics AS
SELECT 
    complexity_level,
    COUNT(*) as document_count,
    SUM(effort_calculated) as total_calculated_hours,
    SUM(effort_optimized) as total_optimized_hours,
    SUM(effort_savings) as total_savings,
    AVG(total_all_fields) as avg_fields,
    AVG(CAST(REPLACE(overall_reuse_rate, '%', '') AS REAL)) as avg_reuse_rate
FROM documents
GROUP BY complexity_level;

-- View for field type distribution
CREATE VIEW field_distribution AS
SELECT 
    'if' as field_type,
    SUM(if_count) as total_count,
    SUM(if_unique) as unique_count,
    SUM(if_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'precedentScript' as field_type,
    SUM(precedent_script_count) as total_count,
    SUM(precedent_script_unique) as unique_count,
    SUM(precedent_script_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'reflection' as field_type,
    SUM(reflection_count) as total_count,
    SUM(reflection_unique) as unique_count,
    SUM(reflection_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'search' as field_type,
    SUM(search_count) as total_count,
    SUM(search_unique) as unique_count,
    SUM(search_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'unbound' as field_type,
    SUM(unbound_count) as total_count,
    SUM(unbound_unique) as unique_count,
    SUM(unbound_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'builtInScript' as field_type,
    SUM(built_in_script_count) as total_count,
    SUM(built_in_script_unique) as unique_count,
    SUM(built_in_script_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'extended' as field_type,
    SUM(extended_count) as total_count,
    SUM(extended_unique) as unique_count,
    SUM(extended_reusable) as reusable_count
FROM documents
UNION ALL
SELECT 
    'scripted' as field_type,
    SUM(scripted_count) as total_count,
    SUM(scripted_unique) as unique_count,
    SUM(scripted_reusable) as reusable_count
FROM documents;
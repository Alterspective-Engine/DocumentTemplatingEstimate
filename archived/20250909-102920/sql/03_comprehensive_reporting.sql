-- ============================================================================
-- COMPREHENSIVE REPORTING SYSTEM FOR ESTIMATEDOC
-- Includes statistical analysis and estimation for unmatched documents
-- ============================================================================

-- ============================================================================
-- PART 1: ENHANCED FIELD ANALYSIS TABLES
-- ============================================================================

-- Table to track which fields are unique vs reusable across documents
CREATE TABLE IF NOT EXISTS field_reusability_analysis (
    field_id INTEGER PRIMARY KEY REFERENCES fields(field_id),
    usage_count INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    is_reusable BOOLEAN GENERATED ALWAYS AS (document_count > 1) STORED,
    is_unique BOOLEAN GENERATED ALWAYS AS (document_count = 1) STORED,
    avg_instances_per_doc DECIMAL(10,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate field reusability analysis
CREATE OR REPLACE FUNCTION analyze_field_reusability()
RETURNS VOID AS $$
BEGIN
    TRUNCATE field_reusability_analysis;
    
    INSERT INTO field_reusability_analysis (field_id, usage_count, document_count, avg_instances_per_doc)
    SELECT 
        f.field_id,
        COALESCE(SUM(df.count), 0) as usage_count,
        COUNT(DISTINCT df.document_id) as document_count,
        CASE 
            WHEN COUNT(DISTINCT df.document_id) > 0 
            THEN ROUND(CAST(SUM(df.count) AS DECIMAL) / COUNT(DISTINCT df.document_id), 2)
            ELSE 0
        END as avg_instances_per_doc
    FROM fields f
    LEFT JOIN document_fields df ON f.field_id = df.field_id
    GROUP BY f.field_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 2: DOCUMENT-LEVEL REUSABILITY METRICS
-- ============================================================================

-- Enhanced document complexity with reusability metrics
CREATE TABLE IF NOT EXISTS document_reusability_metrics (
    document_id INTEGER PRIMARY KEY REFERENCES documents(document_id),
    total_fields INTEGER DEFAULT 0,
    unique_to_doc_fields INTEGER DEFAULT 0,  -- Fields only in this document
    reusable_fields INTEGER DEFAULT 0,       -- Fields used in multiple documents
    reusability_ratio DECIMAL(5,2),         -- Percentage of fields that are reusable
    has_scripts BOOLEAN DEFAULT FALSE,
    script_count INTEGER DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to calculate document reusability metrics
CREATE OR REPLACE FUNCTION calculate_document_reusability(p_document_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_script_count INTEGER;
BEGIN
    -- Check for associated scripts (via precedents)
    SELECT COUNT(DISTINCT ps.script_code) INTO v_script_count
    FROM template_matches tm
    JOIN precedent_scripts ps ON tm.precedent_id = ps.precedent_id
    WHERE tm.document_id = p_document_id;
    
    -- Calculate reusability metrics
    INSERT INTO document_reusability_metrics (
        document_id,
        total_fields,
        unique_to_doc_fields,
        reusable_fields,
        reusability_ratio,
        has_scripts,
        script_count
    )
    SELECT 
        p_document_id,
        COUNT(DISTINCT df.field_id) as total_fields,
        COUNT(DISTINCT CASE WHEN fra.is_unique THEN df.field_id END) as unique_to_doc,
        COUNT(DISTINCT CASE WHEN fra.is_reusable THEN df.field_id END) as reusable,
        CASE 
            WHEN COUNT(DISTINCT df.field_id) > 0 
            THEN ROUND(100.0 * COUNT(DISTINCT CASE WHEN fra.is_reusable THEN df.field_id END) / 
                       COUNT(DISTINCT df.field_id), 2)
            ELSE 0
        END as reusability_ratio,
        v_script_count > 0,
        v_script_count
    FROM document_fields df
    LEFT JOIN field_reusability_analysis fra ON df.field_id = fra.field_id
    WHERE df.document_id = p_document_id
    GROUP BY df.document_id
    ON CONFLICT (document_id) DO UPDATE SET
        total_fields = EXCLUDED.total_fields,
        unique_to_doc_fields = EXCLUDED.unique_to_doc_fields,
        reusable_fields = EXCLUDED.reusable_fields,
        reusability_ratio = EXCLUDED.reusability_ratio,
        has_scripts = EXCLUDED.has_scripts,
        script_count = EXCLUDED.script_count,
        calculated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 3: COMPLEXITY STATISTICS BY STATED LEVEL
-- ============================================================================

-- Table to store complexity level statistics
CREATE TABLE IF NOT EXISTS complexity_level_statistics (
    stated_complexity VARCHAR(50) PRIMARY KEY,
    sample_size INTEGER DEFAULT 0,
    -- Field metrics
    avg_total_fields DECIMAL(10,2),
    stddev_total_fields DECIMAL(10,2),
    min_total_fields INTEGER,
    max_total_fields INTEGER,
    -- Unique/Reusable metrics
    avg_unique_fields DECIMAL(10,2),
    stddev_unique_fields DECIMAL(10,2),
    avg_reusable_fields DECIMAL(10,2),
    stddev_reusable_fields DECIMAL(10,2),
    -- IF statements
    avg_if_statements DECIMAL(10,2),
    stddev_if_statements DECIMAL(10,2),
    -- Scripts
    avg_script_count DECIMAL(10,2),
    stddev_script_count DECIMAL(10,2),
    -- Complexity score
    avg_complexity_score DECIMAL(10,2),
    stddev_complexity_score DECIMAL(10,2),
    -- Confidence intervals (95%)
    ci_lower_total_fields DECIMAL(10,2),
    ci_upper_total_fields DECIMAL(10,2),
    ci_lower_complexity_score DECIMAL(10,2),
    ci_upper_complexity_score DECIMAL(10,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to calculate complexity statistics by stated level
CREATE OR REPLACE FUNCTION calculate_complexity_statistics()
RETURNS VOID AS $$
BEGIN
    TRUNCATE complexity_level_statistics;
    
    INSERT INTO complexity_level_statistics
    SELECT 
        et.stated_complexity,
        COUNT(DISTINCT et.row_id) as sample_size,
        -- Field metrics
        AVG(dc.total_fields) as avg_total_fields,
        STDDEV(dc.total_fields) as stddev_total_fields,
        MIN(dc.total_fields) as min_total_fields,
        MAX(dc.total_fields) as max_total_fields,
        -- Unique/Reusable
        AVG(drm.unique_to_doc_fields) as avg_unique_fields,
        STDDEV(drm.unique_to_doc_fields) as stddev_unique_fields,
        AVG(drm.reusable_fields) as avg_reusable_fields,
        STDDEV(drm.reusable_fields) as stddev_reusable_fields,
        -- IF statements
        AVG(dc.if_statements) as avg_if_statements,
        STDDEV(dc.if_statements) as stddev_if_statements,
        -- Scripts
        AVG(drm.script_count) as avg_script_count,
        STDDEV(drm.script_count) as stddev_script_count,
        -- Complexity score
        AVG(dc.total_complexity_score) as avg_complexity_score,
        STDDEV(dc.total_complexity_score) as stddev_complexity_score,
        -- 95% Confidence intervals (mean ± 1.96 * stddev/sqrt(n))
        AVG(dc.total_fields) - 1.96 * STDDEV(dc.total_fields) / SQRT(COUNT(*)) as ci_lower_total_fields,
        AVG(dc.total_fields) + 1.96 * STDDEV(dc.total_fields) / SQRT(COUNT(*)) as ci_upper_total_fields,
        AVG(dc.total_complexity_score) - 1.96 * STDDEV(dc.total_complexity_score) / SQRT(COUNT(*)) as ci_lower_complexity_score,
        AVG(dc.total_complexity_score) + 1.96 * STDDEV(dc.total_complexity_score) / SQRT(COUNT(*)) as ci_upper_complexity_score,
        CURRENT_TIMESTAMP
    FROM excel_templates et
    JOIN template_matches tm ON et.row_id = tm.excel_row_id
    JOIN document_complexity dc ON tm.document_id = dc.document_id
    LEFT JOIN document_reusability_metrics drm ON tm.document_id = drm.document_id
    WHERE tm.document_id IS NOT NULL
      AND et.stated_complexity IS NOT NULL
    GROUP BY et.stated_complexity;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: COMPREHENSIVE EXCEL ROW REPORT
-- ============================================================================

CREATE OR REPLACE VIEW v_comprehensive_excel_report AS
WITH matched_documents AS (
    -- Get all matched documents with full metrics
    SELECT 
        et.row_id,
        et.template_code,
        et.description,
        et.stated_complexity,
        tm.document_id,
        d.filename,
        tm.match_method,
        tm.match_confidence,
        -- Document complexity metrics
        dc.total_fields,
        dc.unique_fields,
        dc.if_statements,
        dc.nested_if_statements,
        dc.unbound_fields,
        dc.user_input_fields,
        dc.calculated_fields,
        dc.total_complexity_score,
        dc.complexity_rating,
        -- Reusability metrics
        drm.unique_to_doc_fields,
        drm.reusable_fields,
        drm.reusability_ratio,
        drm.has_scripts,
        drm.script_count,
        'Matched' as match_status
    FROM excel_templates et
    JOIN template_matches tm ON et.row_id = tm.excel_row_id
    JOIN documents d ON tm.document_id = d.document_id
    LEFT JOIN document_complexity dc ON d.document_id = dc.document_id
    LEFT JOIN document_reusability_metrics drm ON d.document_id = drm.document_id
    WHERE tm.document_id IS NOT NULL
),
unmatched_documents AS (
    -- Get unmatched documents with estimated metrics
    SELECT 
        et.row_id,
        et.template_code,
        et.description,
        et.stated_complexity,
        NULL::INTEGER as document_id,
        NULL::VARCHAR as filename,
        tm.match_method,
        tm.match_confidence,
        -- Estimated metrics from statistics
        cls.avg_total_fields::INTEGER as total_fields,
        NULL::INTEGER as unique_fields,  -- Will be calculated
        cls.avg_if_statements::INTEGER as if_statements,
        NULL::INTEGER as nested_if_statements,
        NULL::INTEGER as unbound_fields,
        NULL::INTEGER as user_input_fields,
        NULL::INTEGER as calculated_fields,
        cls.avg_complexity_score::INTEGER as total_complexity_score,
        CASE 
            WHEN cls.avg_complexity_score = 0 THEN 'Simple'
            WHEN cls.avg_complexity_score < 10 THEN 'Low'
            WHEN cls.avg_complexity_score < 30 THEN 'Medium'
            WHEN cls.avg_complexity_score < 50 THEN 'High'
            ELSE 'Very High'
        END as complexity_rating,
        -- Estimated reusability metrics
        cls.avg_unique_fields::INTEGER as unique_to_doc_fields,
        cls.avg_reusable_fields::INTEGER as reusable_fields,
        ROUND(100.0 * cls.avg_reusable_fields / NULLIF(cls.avg_total_fields, 0), 2) as reusability_ratio,
        cls.avg_script_count > 0 as has_scripts,
        cls.avg_script_count::INTEGER as script_count,
        'Estimated' as match_status
    FROM excel_templates et
    LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
    LEFT JOIN complexity_level_statistics cls ON et.stated_complexity = cls.stated_complexity
    WHERE tm.document_id IS NULL
      AND et.stated_complexity IS NOT NULL
)
SELECT * FROM matched_documents
UNION ALL
SELECT * FROM unmatched_documents
ORDER BY row_id;

-- ============================================================================
-- PART 5: STATISTICAL SUMMARY REPORT
-- ============================================================================

CREATE OR REPLACE VIEW v_complexity_statistical_summary AS
SELECT 
    cls.stated_complexity,
    cls.sample_size,
    -- Field statistics with confidence
    ROUND(cls.avg_total_fields, 1) as avg_total_fields,
    ROUND(cls.stddev_total_fields, 1) as stddev_total_fields,
    CONCAT('[', ROUND(cls.ci_lower_total_fields, 1), '-', ROUND(cls.ci_upper_total_fields, 1), ']') as ci_95_total_fields,
    -- Reusability statistics
    ROUND(cls.avg_unique_fields, 1) as avg_unique_fields,
    ROUND(cls.avg_reusable_fields, 1) as avg_reusable_fields,
    ROUND(100.0 * cls.avg_reusable_fields / NULLIF(cls.avg_total_fields, 0), 1) as avg_reusability_pct,
    -- Complexity statistics
    ROUND(cls.avg_if_statements, 1) as avg_if_statements,
    ROUND(cls.avg_script_count, 1) as avg_script_count,
    ROUND(cls.avg_complexity_score, 1) as avg_complexity_score,
    ROUND(cls.stddev_complexity_score, 1) as stddev_complexity_score,
    CONCAT('[', ROUND(cls.ci_lower_complexity_score, 1), '-', ROUND(cls.ci_upper_complexity_score, 1), ']') as ci_95_complexity_score,
    -- Coefficient of variation (relative variability)
    ROUND(100.0 * cls.stddev_complexity_score / NULLIF(cls.avg_complexity_score, 0), 1) as cv_complexity_pct
FROM complexity_level_statistics cls
ORDER BY 
    CASE cls.stated_complexity
        WHEN 'Simple' THEN 1
        WHEN 'Moderate' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Complex' THEN 4
        ELSE 5
    END;

-- ============================================================================
-- PART 6: ESTIMATION QUALITY METRICS
-- ============================================================================

CREATE OR REPLACE VIEW v_estimation_quality AS
WITH matched_by_complexity AS (
    SELECT 
        et.stated_complexity,
        COUNT(DISTINCT CASE WHEN tm.document_id IS NOT NULL THEN et.row_id END) as matched_count,
        COUNT(DISTINCT CASE WHEN tm.document_id IS NULL THEN et.row_id END) as unmatched_count,
        COUNT(DISTINCT et.row_id) as total_count
    FROM excel_templates et
    LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
    WHERE et.stated_complexity IS NOT NULL
    GROUP BY et.stated_complexity
)
SELECT 
    mbc.stated_complexity,
    mbc.matched_count,
    mbc.unmatched_count,
    mbc.total_count,
    ROUND(100.0 * mbc.matched_count / NULLIF(mbc.total_count, 0), 1) as match_rate_pct,
    cls.sample_size as statistical_sample_size,
    CASE 
        WHEN cls.sample_size >= 30 THEN 'High'
        WHEN cls.sample_size >= 10 THEN 'Medium'
        WHEN cls.sample_size >= 5 THEN 'Low'
        ELSE 'Very Low'
    END as estimation_confidence,
    ROUND(cls.stddev_complexity_score / NULLIF(cls.avg_complexity_score, 0) * 100, 1) as variability_pct,
    CASE 
        WHEN cls.stddev_complexity_score / NULLIF(cls.avg_complexity_score, 0) < 0.2 THEN 'Very Consistent'
        WHEN cls.stddev_complexity_score / NULLIF(cls.avg_complexity_score, 0) < 0.4 THEN 'Consistent'
        WHEN cls.stddev_complexity_score / NULLIF(cls.avg_complexity_score, 0) < 0.6 THEN 'Moderate'
        ELSE 'High Variance'
    END as consistency_rating
FROM matched_by_complexity mbc
LEFT JOIN complexity_level_statistics cls ON mbc.stated_complexity = cls.stated_complexity
ORDER BY 
    CASE mbc.stated_complexity
        WHEN 'Simple' THEN 1
        WHEN 'Moderate' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Complex' THEN 4
        ELSE 5
    END;

-- ============================================================================
-- PART 7: HELPER FUNCTIONS TO POPULATE ALL METRICS
-- ============================================================================

CREATE OR REPLACE FUNCTION refresh_all_reporting_metrics()
RETURNS VOID AS $$
DECLARE
    v_doc_id INTEGER;
BEGIN
    -- Step 1: Analyze field reusability
    PERFORM analyze_field_reusability();
    RAISE NOTICE 'Field reusability analysis completed';
    
    -- Step 2: Calculate document reusability metrics
    FOR v_doc_id IN SELECT document_id FROM documents
    LOOP
        PERFORM calculate_document_reusability(v_doc_id);
    END LOOP;
    RAISE NOTICE 'Document reusability metrics calculated';
    
    -- Step 3: Calculate complexity statistics by stated level
    PERFORM calculate_complexity_statistics();
    RAISE NOTICE 'Complexity statistics calculated';
    
    -- Refresh materialized views if any
    -- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_name;
    
    RAISE NOTICE 'All reporting metrics refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 8: FINAL COMPREHENSIVE REPORT QUERY
-- ============================================================================

-- This query provides the complete report with all metrics
CREATE OR REPLACE VIEW v_final_excel_comprehensive_report AS
SELECT 
    cer.row_id,
    cer.template_code,
    cer.description,
    cer.stated_complexity,
    cer.match_status,
    cer.match_method,
    cer.match_confidence,
    -- Document info
    cer.document_id,
    cer.filename,
    -- Core metrics
    cer.total_fields,
    cer.unique_to_doc_fields,
    cer.reusable_fields,
    cer.reusability_ratio,
    cer.if_statements,
    cer.has_scripts,
    cer.script_count,
    cer.total_complexity_score,
    cer.complexity_rating,
    -- Statistical context (for estimated rows)
    CASE 
        WHEN cer.match_status = 'Estimated' THEN cls.sample_size
        ELSE NULL
    END as estimation_sample_size,
    CASE 
        WHEN cer.match_status = 'Estimated' THEN ROUND(cls.stddev_total_fields, 1)
        ELSE NULL
    END as fields_stddev,
    CASE 
        WHEN cer.match_status = 'Estimated' THEN ROUND(cls.stddev_complexity_score, 1)
        ELSE NULL
    END as complexity_stddev,
    CASE 
        WHEN cer.match_status = 'Estimated' THEN 
            CONCAT('[', ROUND(cls.ci_lower_complexity_score, 0), '-', ROUND(cls.ci_upper_complexity_score, 0), ']')
        ELSE NULL
    END as complexity_ci_95,
    CASE 
        WHEN cer.match_status = 'Estimated' AND cls.sample_size >= 30 THEN 'High'
        WHEN cer.match_status = 'Estimated' AND cls.sample_size >= 10 THEN 'Medium'
        WHEN cer.match_status = 'Estimated' AND cls.sample_size >= 5 THEN 'Low'
        WHEN cer.match_status = 'Estimated' THEN 'Very Low'
        ELSE 'Actual'
    END as data_confidence
FROM v_comprehensive_excel_report cer
LEFT JOIN complexity_level_statistics cls ON cer.stated_complexity = cls.stated_complexity
ORDER BY cer.row_id;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_field_reusability_usage ON field_reusability_analysis(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_field_reusability_docs ON field_reusability_analysis(document_count DESC);
CREATE INDEX IF NOT EXISTS idx_doc_reusability_doc ON document_reusability_metrics(document_id);
CREATE INDEX IF NOT EXISTS idx_complexity_stats_level ON complexity_level_statistics(stated_complexity);
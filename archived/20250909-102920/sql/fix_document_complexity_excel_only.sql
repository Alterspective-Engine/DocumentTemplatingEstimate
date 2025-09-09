-- Fix document_complexity to ONLY include Excel-linked documents
-- ================================================================
-- CRITICAL: We must only analyze the 235 documents referenced in Excel templates

-- First, clear the existing data
TRUNCATE TABLE document_complexity;

-- Now insert ONLY for Excel-linked documents
INSERT INTO document_complexity (
    document_id,
    total_fields,
    unique_fields,
    reusable_fields,
    docvariable_fields,
    mergefield_fields,
    if_statements,
    nested_if_statements,
    user_input_fields,
    calculated_fields,
    total_complexity_score,
    complexity_rating
)
WITH excel_documents AS (
    -- CRITICAL: Only documents linked to Excel templates
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    d.document_id,
    -- Total fields in document
    COUNT(DISTINCT df.field_id) as total_fields,
    
    -- Unique fields (used only in this document among Excel docs)
    COUNT(DISTINCT CASE 
        WHEN f.field_id IN (
            SELECT field_id 
            FROM document_fields df2 
            WHERE df2.document_id IN (SELECT document_id FROM excel_documents)
            GROUP BY field_id 
            HAVING COUNT(DISTINCT document_id) = 1
        ) THEN f.field_id 
    END) as unique_fields,
    
    -- Reusable fields (used in multiple Excel documents)
    COUNT(DISTINCT CASE 
        WHEN f.field_id IN (
            SELECT field_id 
            FROM document_fields df2 
            WHERE df2.document_id IN (SELECT document_id FROM excel_documents)
            GROUP BY field_id 
            HAVING COUNT(DISTINCT document_id) > 1
        ) THEN f.field_id 
    END) as reusable_fields,
    
    -- Field type counts
    COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) as docvariable_fields,
    COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) as mergefield_fields,
    COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) as if_statements,
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%IF %' 
        AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
        THEN f.field_id 
    END) as nested_if_statements,
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
        THEN f.field_id 
    END) as user_input_fields,
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
        THEN f.field_id 
    END) as calculated_fields,
    
    -- Calculate total complexity score
    (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) * 3) +
    (COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%IF %' 
        AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
        THEN f.field_id END) * 2) +
    (COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
        THEN f.field_id END) * 2) +
    (COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
        THEN f.field_id END) * 2) +
    (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) * 1) +
    (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) * 1)
    as total_complexity_score,
    
    -- Assign complexity rating
    CASE 
        WHEN (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) * 3) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%IF %' 
                AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) * 1) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) * 1) <= 10 
        THEN 'Simple'
        WHEN (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) * 3) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%IF %' 
                AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) * 1) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) * 1) <= 25 
        THEN 'Medium'
        WHEN (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) * 3) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%IF %' 
                AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE 
                WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
                THEN f.field_id END) * 2) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) * 1) +
             (COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) * 1) <= 50 
        THEN 'High'
        ELSE 'Very High'
    END as complexity_rating
FROM documents d
LEFT JOIN document_fields df ON d.document_id = df.document_id
LEFT JOIN fields f ON df.field_id = f.field_id
WHERE d.document_id IN (SELECT document_id FROM excel_documents)  -- CRITICAL FILTER
GROUP BY d.document_id;

-- Verify the fix
SELECT 
    'Documents in complexity table' as metric,
    COUNT(*) as count,
    CASE 
        WHEN COUNT(*) = 235 THEN '✅ CORRECT - Only Excel documents'
        ELSE '❌ ERROR - Should be exactly 235'
    END as status
FROM document_complexity;

-- Show complexity distribution for Excel documents only
SELECT 
    complexity_rating,
    COUNT(*) as document_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM document_complexity), 1) || '%' as percentage
FROM document_complexity
GROUP BY complexity_rating
ORDER BY 
    CASE complexity_rating
        WHEN 'Simple' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'High' THEN 3
        WHEN 'Very High' THEN 4
    END;
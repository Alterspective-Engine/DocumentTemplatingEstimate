-- Populate document_complexity table with actual calculations
-- This analyzes each document's fields to calculate complexity metrics

-- First, clear existing data
TRUNCATE TABLE document_complexity;

-- Insert complexity calculations for all documents
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
SELECT 
    d.document_id,
    -- Total fields in document
    COUNT(DISTINCT df.field_id) as total_fields,
    
    -- Unique fields (used only in this document)
    COUNT(DISTINCT CASE 
        WHEN f.field_id IN (
            SELECT field_id 
            FROM document_fields df2 
            GROUP BY field_id 
            HAVING COUNT(DISTINCT document_id) = 1
        ) THEN f.field_id 
    END) as unique_fields,
    
    -- Reusable fields (used in multiple documents)
    COUNT(DISTINCT CASE 
        WHEN f.field_id IN (
            SELECT field_id 
            FROM document_fields df2 
            GROUP BY field_id 
            HAVING COUNT(DISTINCT document_id) > 1
        ) THEN f.field_id 
    END) as reusable_fields,
    
    -- DOCVARIABLE fields
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id 
    END) as docvariable_fields,
    
    -- MERGEFIELD fields  
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id 
    END) as mergefield_fields,
    
    -- IF statements
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%IF %' THEN f.field_id 
    END) as if_statements,
    
    -- Nested IF statements (IF within IF)
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%IF %' 
        AND (LENGTH(f.field_code) - LENGTH(REPLACE(f.field_code, 'IF ', ''))) / 3 > 1
        THEN f.field_id 
    END) as nested_if_statements,
    
    -- User input fields (ASK, FILLIN)
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' 
        THEN f.field_id 
    END) as user_input_fields,
    
    -- Calculated fields (contains = or FORMULA)
    COUNT(DISTINCT CASE 
        WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' 
        THEN f.field_id 
    END) as calculated_fields,
    
    -- Calculate total complexity score
    -- IF statements: 3 points each
    -- Nested IF: 2 additional points each
    -- User input: 2 points each
    -- Calculated: 2 points each
    -- DOCVARIABLE: 1 point each
    -- MERGEFIELD: 1 point each
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
    
    -- Assign complexity rating based on score
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
GROUP BY d.document_id;

-- Add some statistics
SELECT 
    'Documents analyzed' as metric,
    COUNT(*) as count
FROM document_complexity
UNION ALL
SELECT 
    'Documents with fields',
    COUNT(*)
FROM document_complexity
WHERE total_fields > 0
UNION ALL
SELECT 
    'Simple documents',
    COUNT(*)
FROM document_complexity
WHERE complexity_rating = 'Simple'
UNION ALL
SELECT 
    'Medium documents',
    COUNT(*)
FROM document_complexity
WHERE complexity_rating = 'Medium'
UNION ALL
SELECT 
    'High complexity documents',
    COUNT(*)
FROM document_complexity
WHERE complexity_rating = 'High'
UNION ALL
SELECT 
    'Very High complexity documents',
    COUNT(*)
FROM document_complexity
WHERE complexity_rating = 'Very High';

-- Show sample of populated data
SELECT 
    dc.document_id,
    d.filename,
    dc.total_fields,
    dc.if_statements,
    dc.total_complexity_score,
    dc.complexity_rating
FROM document_complexity dc
JOIN documents d ON dc.document_id = d.document_id
WHERE dc.total_fields > 0
ORDER BY dc.total_complexity_score DESC
LIMIT 10;
-- Validation Script: Ensure ALL Reporting Uses Excel-Linked Documents Only
-- ========================================================================
-- The Excel templates are the CRITICAL documents for effort reporting
-- We must ONLY use the 235 documents linked to Excel, not all 782

-- 1. Verify Excel Document Count
-- Expected: 235 documents (not 782)
SELECT 
    'Excel-Linked Documents' as metric,
    COUNT(DISTINCT tm.document_id) as value,
    CASE 
        WHEN COUNT(DISTINCT tm.document_id) = 235 THEN '✅ CORRECT' 
        ELSE '❌ ERROR - Should be 235' 
    END as status
FROM template_matches tm
WHERE tm.document_id IS NOT NULL;

-- 2. Compare Total Documents vs Excel Documents
SELECT 
    'Document Filtering Check' as metric,
    (SELECT COUNT(*) FROM documents) as total_in_db,
    (SELECT COUNT(DISTINCT document_id) FROM template_matches WHERE document_id IS NOT NULL) as excel_linked,
    ROUND(100.0 * (SELECT COUNT(DISTINCT document_id) FROM template_matches WHERE document_id IS NOT NULL) / 
          (SELECT COUNT(*) FROM documents), 1) || '%' as percentage_used;

-- 3. Verify Field Count is from Excel Documents Only
-- Should be ~4,809 not 11,653
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    'Field Count Validation' as metric,
    (SELECT COUNT(*) FROM fields) as all_fields_in_db,
    (SELECT COUNT(DISTINCT f.field_id) 
     FROM fields f 
     JOIN document_fields df ON f.field_id = df.field_id
     WHERE df.document_id IN (SELECT document_id FROM excel_documents)) as excel_doc_fields,
    CASE 
        WHEN (SELECT COUNT(DISTINCT f.field_id) 
              FROM fields f 
              JOIN document_fields df ON f.field_id = df.field_id
              WHERE df.document_id IN (SELECT document_id FROM excel_documents)) < 5000 
        THEN '✅ Using Excel filter correctly'
        ELSE '❌ ERROR - Not filtering properly'
    END as status;

-- 4. Check Complexity Calculations
-- Should only include Excel-linked documents
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    'Complexity Analysis Scope' as metric,
    COUNT(DISTINCT dc.document_id) as docs_with_complexity,
    COUNT(DISTINCT CASE WHEN dc.document_id IN (SELECT document_id FROM excel_documents) 
                        THEN dc.document_id END) as excel_docs_with_complexity,
    CASE 
        WHEN COUNT(DISTINCT dc.document_id) > 300 
        THEN '❌ Including non-Excel documents!'
        ELSE '✅ Correctly filtered'
    END as status
FROM document_complexity dc
WHERE dc.total_fields > 0;

-- 5. Verify Field Reusability is Excel-Scoped
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
),
excel_field_usage AS (
    SELECT 
        f.field_id,
        COUNT(DISTINCT df.document_id) as doc_count
    FROM fields f
    JOIN document_fields df ON f.field_id = df.field_id
    WHERE df.document_id IN (SELECT document_id FROM excel_documents)
    GROUP BY f.field_id
),
all_field_usage AS (
    SELECT 
        f.field_id,
        COUNT(DISTINCT df.document_id) as doc_count
    FROM fields f
    JOIN document_fields df ON f.field_id = df.field_id
    GROUP BY f.field_id
)
SELECT 
    'Field Reusability Scope' as metric,
    (SELECT COUNT(*) FROM all_field_usage WHERE doc_count > 1) as all_shared_fields,
    (SELECT COUNT(*) FROM excel_field_usage WHERE doc_count > 1) as excel_shared_fields,
    CASE 
        WHEN (SELECT COUNT(*) FROM excel_field_usage WHERE doc_count > 1) < 
             (SELECT COUNT(*) FROM all_field_usage WHERE doc_count > 1)
        THEN '✅ Correctly using Excel scope'
        ELSE '❌ ERROR - Not filtering'
    END as status;

-- 6. Template Match Statistics
SELECT 
    'Template Matching' as metric,
    COUNT(*) as total_excel_templates,
    COUNT(CASE WHEN tm.document_id IS NOT NULL THEN 1 END) as matched_templates,
    ROUND(100.0 * COUNT(CASE WHEN tm.document_id IS NOT NULL THEN 1 END) / COUNT(*), 1) || '%' as match_rate
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id;

-- 7. Show Distribution of Excel Documents by Complexity
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    COALESCE(dc.complexity_rating, 'No Rating') as complexity,
    COUNT(DISTINCT ed.document_id) as document_count,
    ROUND(100.0 * COUNT(DISTINCT ed.document_id) / 
          (SELECT COUNT(*) FROM excel_documents), 1) || '%' as percentage
FROM excel_documents ed
LEFT JOIN document_complexity dc ON ed.document_id = dc.document_id
GROUP BY dc.complexity_rating
ORDER BY 
    CASE dc.complexity_rating
        WHEN 'Simple' THEN 1
        WHEN 'Low' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'High' THEN 4
        WHEN 'Very High' THEN 5
        ELSE 6
    END;

-- 8. CRITICAL CHECK: Ensure NO Non-Excel Documents in Reports
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
),
non_excel_documents AS (
    SELECT d.document_id, d.filename
    FROM documents d
    WHERE d.document_id NOT IN (SELECT document_id FROM excel_documents)
)
SELECT 
    'Non-Excel Documents Check' as metric,
    COUNT(*) as non_excel_count,
    CASE 
        WHEN COUNT(*) = 547 THEN '✅ Correctly identified 547 non-Excel docs to exclude'
        ELSE '❌ ERROR - Expected 547 non-Excel documents'
    END as status,
    'These ' || COUNT(*) || ' documents must NEVER appear in effort reports' as note
FROM non_excel_documents;

-- 9. Summary Dashboard
SELECT 
    '=== EXCEL FILTERING VALIDATION SUMMARY ===' as report,
    '' as value
UNION ALL
SELECT 
    'Excel Templates (Source)', 
    COUNT(*)::text || ' rows'
FROM excel_templates
UNION ALL
SELECT 
    'Matched to Documents', 
    COUNT(DISTINCT document_id)::text || ' docs (235 expected)'
FROM template_matches
WHERE document_id IS NOT NULL
UNION ALL
SELECT 
    'Fields from Excel Docs', 
    COUNT(DISTINCT f.field_id)::text || ' fields (~4,809 expected)'
FROM fields f
JOIN document_fields df ON f.field_id = df.field_id
WHERE df.document_id IN (
    SELECT DISTINCT document_id 
    FROM template_matches 
    WHERE document_id IS NOT NULL
)
UNION ALL
SELECT 
    'Match Success Rate',
    ROUND(100.0 * COUNT(CASE WHEN tm.document_id IS NOT NULL THEN 1 END) / COUNT(*), 1) || '%'
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
UNION ALL
SELECT 
    '⚠️ CRITICAL RULE',
    'ONLY use 235 Excel docs for ALL reporting';
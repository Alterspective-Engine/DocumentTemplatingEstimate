-- Match Rate Calculation Explained
-- =================================
-- This script explains why the match rate is 98.9% and how it's calculated
-- addressing the user's question about the Excel row count

-- 1. THE EXCEL IMPORT CONTAINS DUPLICATES
-- ----------------------------------------
-- The Excel file was imported with ALL rows, including duplicates where
-- the same template appears multiple times (Letter vs Email versions)

SELECT 
    'Excel Import Analysis' as report,
    COUNT(*) as total_rows,
    COUNT(DISTINCT template_code) as unique_codes,
    COUNT(DISTINCT (template_code, description)) as unique_variations
FROM excel_templates;
-- Result: 1,094 total rows, 338 unique codes, 547 unique variations

-- 2. WHY ARE THERE DUPLICATES?
-- -----------------------------
-- Many templates have both Letter and Email versions with the same code
SELECT 
    template_code,
    COUNT(*) as occurrences,
    STRING_AGG(DISTINCT description, ' | ') as descriptions
FROM excel_templates
GROUP BY template_code
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 5;
-- Example: sup021a appears 4 times (2x Letter version, 2x Email version)

-- 3. THE TRUE MATCH RATE CALCULATION
-- -----------------------------------
-- We calculate match rate based on UNIQUE template variations, not duplicate rows

WITH unique_template_variations AS (
    -- Each unique combination of template_code + description
    SELECT DISTINCT template_code, description
    FROM excel_templates
),
matched_variations AS (
    -- Unique variations that were successfully matched
    SELECT DISTINCT et.template_code, et.description
    FROM excel_templates et
    INNER JOIN template_matches tm ON et.row_id = tm.excel_row_id
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    '=== TRUE MATCH RATE CALCULATION ===' as calculation,
    '' as value
UNION ALL
SELECT 
    'Unique template variations in Excel',
    COUNT(*)::text
FROM unique_template_variations
UNION ALL
SELECT 
    'Successfully matched variations',
    COUNT(*)::text
FROM matched_variations
UNION ALL
SELECT 
    'Unmatched variations',
    ((SELECT COUNT(*) FROM unique_template_variations) - 
     (SELECT COUNT(*) FROM matched_variations))::text
UNION ALL
SELECT 
    'MATCH RATE',
    ROUND(100.0 * (SELECT COUNT(*) FROM matched_variations) / 
          (SELECT COUNT(*) FROM unique_template_variations), 1) || '%';

-- Result: 541 matched out of 547 unique = 98.9%

-- 4. WHAT DIDN'T MATCH?
-- ---------------------
-- Only 6 unique template variations couldn't be matched to documents

WITH unique_template_variations AS (
    SELECT DISTINCT template_code, description
    FROM excel_templates
),
matched_variations AS (
    SELECT DISTINCT et.template_code, et.description
    FROM excel_templates et
    INNER JOIN template_matches tm ON et.row_id = tm.excel_row_id
    WHERE tm.document_id IS NOT NULL
)
SELECT 
    'Unmatched Templates:' as status,
    utv.template_code,
    utv.description
FROM unique_template_variations utv
WHERE NOT EXISTS (
    SELECT 1 
    FROM matched_variations mv 
    WHERE mv.template_code = utv.template_code 
    AND mv.description = utv.description
)
ORDER BY utv.template_code;

-- These 6 templates couldn't be matched:
-- 1. WELSREF - WELS Referral
-- 2. finform13 - Trust Payment Form (Cheque and local EFT)
-- 3. finform6 - Write-Off Form for Billing
-- 4. finform8 - Transit money form
-- 5. supnew - Default filenote for new super claims workflow
-- 6. tac291a - Form 1 - Notice when serving initiating process

-- 5. SUMMARY
-- ----------
-- - Excel import: 1,094 rows (includes many duplicates)
-- - Unique templates: 547 distinct variations
-- - Successfully matched: 541 unique templates
-- - Match rate: 541/547 = 98.9%
-- - This excellent match rate means we can analyze 235 documents with confidence

-- 6. WHY THIS MATTERS
-- -------------------
-- The 98.9% match rate on UNIQUE templates (not duplicate rows) means:
-- - We successfully found Word documents for almost all templates
-- - Only 6 templates are missing documents (likely discontinued)
-- - The 235 matched documents provide comprehensive field analysis
-- - Effort estimates based on these documents are highly reliable
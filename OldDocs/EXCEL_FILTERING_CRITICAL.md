# ⚠️ CRITICAL: Excel Documents ONLY for All Reporting

## The Golden Rule
**ALL effort reporting and calculations MUST use ONLY the 235 Excel-referenced documents, NOT all 782 documents in the database.**

## Why This Matters
The Excel templates are the **SOLE SOURCE OF TRUTH** for effort estimation. The other 547 documents are:
- Test files
- Unused templates
- Legacy documents
- Not relevant for costing

## The Numbers That Matter

### ✅ CORRECT Numbers (Excel-Filtered)
- **Documents**: 235 (not 782)
- **Fields**: 4,809 (not 11,653)
- **Templates**: 1,094 Excel rows
- **Matched**: 1,082 (98.9% success rate)
- **Unmatched**: 12 templates

### ❌ WRONG Numbers (Unfiltered)
- 782 total documents - **DO NOT USE**
- 11,653 total fields - **DO NOT USE**
- 641 documents with fields - **DO NOT USE**

## How We Filter

### SQL Pattern - ALWAYS Use This CTE
```sql
WITH excel_documents AS (
    -- CRITICAL: Only documents linked to Excel templates
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
-- Then use: WHERE document_id IN (SELECT document_id FROM excel_documents)
```

### Backend API - Already Filtered ✅
All API endpoints at `http://localhost:3001/api` are correctly filtered:
- `/stats/overview` - Shows 235 documents
- `/stats/field-reusability` - Analyzes 4,809 fields
- `/templates/browse` - Only Excel templates

### Database Tables

#### Core Tables
- `excel_templates` - 1,094 rows (source of truth)
- `template_matches` - Links Excel to documents
- `documents` - 782 total (but only use 235!)
- `fields` - 11,653 total (but only use 4,809!)

#### Filtered Results
- `document_complexity` - Now correctly has 235 rows (was 782, now fixed)
- All queries use `excel_documents` CTE

## Validation Queries

### Quick Check - Are We Using Excel Filter?
```sql
-- Should return 235, not 782
SELECT COUNT(DISTINCT tm.document_id) 
FROM template_matches tm 
WHERE tm.document_id IS NOT NULL;
```

### Field Count Check
```sql
-- Should return ~4,809, not 11,653
WITH excel_documents AS (
    SELECT DISTINCT tm.document_id
    FROM template_matches tm
    WHERE tm.document_id IS NOT NULL
)
SELECT COUNT(DISTINCT f.field_id)
FROM fields f
JOIN document_fields df ON f.field_id = df.field_id
WHERE df.document_id IN (SELECT document_id FROM excel_documents);
```

## Implementation Status

### ✅ Completed
1. Backend API filtered to Excel documents
2. Database queries use Excel CTE
3. Document complexity table fixed (235 rows)
4. Evidence system shows filtered queries
5. Validation script confirms filtering

### 🔍 Verification
Run `psql -U estimatedoc_user -d estimatedoc -f sql/validate_excel_filtering.sql` to verify.

## Dashboard Impact

### What Users See
- **235** Documents (was showing 782)
- **4,809** Fields (was showing 11,653)
- **98.9%** Match rate (unchanged)
- **Complexity scores** from Excel docs only

### Info Icons Show
Every data value has an info icon (ℹ️) that when clicked shows:
- The filtered SQL query
- Confirmation it's Excel-only
- Exact calculation method

## The Rule Going Forward

**NEVER** create a query, report, or calculation without:
1. Using the `excel_documents` CTE
2. Filtering to 235 documents
3. Showing only 4,809 fields
4. Documenting the Excel filter in comments

## Why 98.9% Match Rate is Excellent

- **1,082 of 1,094** Excel templates matched
- Only **12 templates** couldn't be matched
- These 12 can use statistical estimates
- The 235 matched documents provide full field-level analysis

## Remember

**Excel templates are the ONLY source for effort reporting.**

Everything else is noise.
# PostgreSQL Database Import Plan for EstimateDoc

## Executive Summary
This plan outlines the strategy to import all EstimateDoc data into PostgreSQL, incorporating the Excel→Dataset matching guidance to create a comprehensive analytics platform for legal document complexity analysis and cost estimation.

## Data Sources Overview

### Primary Data Sources
1. **Excel Template Requirements** (`Super Template Requirements_received 23072025.xlsx`)
   - 547 rows of template specifications
   - Contains: Template codes, descriptions, complexity ratings

2. **SQL Export JSON Files** (`SQLExport/`)
   - `dbo_Documents.json`: 782 document records
   - `dbo_Fields.json`: 11,653 field definitions  
   - `dbo_DocumentFields.json`: 19,614 relationships
   - `combined_analysis.json`: Aggregated statistics

3. **ExportSandI Manifest** (`ExportSandI.Manifest.xml`)
   - Authoritative list of precedents with codes and names
   - 400+ precedent entries with metadata

4. **Precedent Manifests** (`ExportSandI/Precedents/*/manifest.xml`)
   - 203 individual precedent XML files
   - Contains precedent metadata and configuration

5. **Script Manifests** (`ExportSandI/Scripts/*/manifest.xml`)
   - 207 automation script definitions
   - Base64-encoded C# code

## PostgreSQL Database Schema Design

### Core Tables

```sql
-- 1. Documents table (from dbo_Documents.json)
CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    basename VARCHAR(255) GENERATED ALWAYS AS (LOWER(REGEXP_REPLACE(filename, '^.*/', ''))) STORED,
    file_extension VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_basename (basename),
    INDEX idx_filename (filename)
);

-- 2. Fields table (from dbo_Fields.json)
CREATE TABLE fields (
    field_id INTEGER PRIMARY KEY,
    field_code TEXT NOT NULL,
    field_result TEXT,
    field_type VARCHAR(50),
    is_docvariable BOOLEAN GENERATED ALWAYS AS (field_code ILIKE '%DOCVARIABLE%') STORED,
    is_mergefield BOOLEAN GENERATED ALWAYS AS (field_code ILIKE '%MERGEFIELD%') STORED,
    has_if_statement BOOLEAN GENERATED ALWAYS AS (field_code ILIKE '%IF%') STORED,
    has_calculation BOOLEAN GENERATED ALWAYS AS (
        field_code LIKE '%+%' OR field_code LIKE '%-%' OR 
        field_code LIKE '%*%' OR field_code LIKE '%/%'
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Document-Field relationships (from dbo_DocumentFields.json)
CREATE TABLE document_fields (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(document_id),
    field_id INTEGER REFERENCES fields(field_id),
    count INTEGER DEFAULT 1,
    UNIQUE(document_id, field_id),
    INDEX idx_doc_field (document_id, field_id)
);

-- 4. Precedents table (from ExportSandI.Manifest.xml)
CREATE TABLE precedents (
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
    normalized_name VARCHAR(255) GENERATED ALWAYS AS (LOWER(name)) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prec_code (code),
    INDEX idx_prec_name (normalized_name)
);

-- 5. Excel template requirements
CREATE TABLE excel_templates (
    row_id SERIAL PRIMARY KEY,
    sheet_name VARCHAR(100),
    row_number INTEGER,
    template_code VARCHAR(50),
    description TEXT,
    stated_complexity VARCHAR(50),
    excel_code VARCHAR(50),      -- Extracted numeric code
    excel_name VARCHAR(100),     -- Extracted Sup name
    excel_filename VARCHAR(255), -- Extracted filename
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Template matching results (implements matching guidance)
CREATE TABLE template_matches (
    match_id SERIAL PRIMARY KEY,
    excel_row_id INTEGER REFERENCES excel_templates(row_id),
    document_id INTEGER REFERENCES documents(document_id),
    precedent_id INTEGER REFERENCES precedents(precedent_id),
    candidate_filename VARCHAR(255),
    match_method VARCHAR(50), -- filename/code_manifest/sup_manifest/name_value/zip_only
    match_confidence VARCHAR(20), -- High/Medium/Low
    unmatched_reason VARCHAR(100),
    zip_rel_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_match_excel (excel_row_id),
    INDEX idx_match_doc (document_id)
);

-- 7. Complexity metrics (calculated)
CREATE TABLE document_complexity (
    complexity_id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(document_id) UNIQUE,
    total_fields INTEGER,
    unique_fields INTEGER,
    reusable_fields INTEGER,
    docvariable_fields INTEGER,
    mergefield_fields INTEGER,
    if_statements INTEGER,
    nested_if_statements INTEGER,
    unbound_fields INTEGER,
    user_input_fields INTEGER,
    calculated_fields INTEGER,
    complex_fields INTEGER,
    avg_field_length DECIMAL(10,2),
    max_field_length INTEGER,
    total_complexity_score INTEGER,
    complexity_rating VARCHAR(20), -- Simple/Low/Medium/High/Very High
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_complexity_doc (document_id),
    INDEX idx_complexity_rating (complexity_rating)
);

-- 8. Scripts table (from Scripts manifests)
CREATE TABLE scripts (
    script_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(50),
    version INTEGER,
    author VARCHAR(100),
    script_text TEXT, -- Decoded from base64
    format INTEGER,
    created TIMESTAMP,
    updated TIMESTAMP,
    rowguid UUID
);

-- 9. Precedent scripts relationship
CREATE TABLE precedent_scripts (
    id SERIAL PRIMARY KEY,
    precedent_id INTEGER REFERENCES precedents(precedent_id),
    script_code VARCHAR(50),
    execution_order INTEGER,
    UNIQUE(precedent_id, script_code)
);

-- 10. Audit and analytics views
CREATE MATERIALIZED VIEW template_analytics AS
SELECT 
    et.row_id,
    et.template_code,
    et.description,
    et.stated_complexity,
    tm.document_id,
    d.filename,
    tm.match_method,
    tm.match_confidence,
    dc.total_fields,
    dc.unique_fields,
    dc.if_statements,
    dc.unbound_fields,
    dc.total_complexity_score,
    dc.complexity_rating as calculated_complexity,
    CASE 
        WHEN et.stated_complexity = dc.complexity_rating THEN 'Match'
        ELSE 'Mismatch'
    END as complexity_agreement
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
LEFT JOIN documents d ON tm.document_id = d.document_id
LEFT JOIN document_complexity dc ON d.document_id = dc.document_id;

-- Create indexes for performance
CREATE INDEX idx_template_analytics_code ON template_analytics(template_code);
CREATE INDEX idx_template_analytics_complexity ON template_analytics(calculated_complexity);
```

## Data Import Strategy

### Phase 1: Core Data Import
1. **Documents Import**
   ```python
   # Load dbo_Documents.json
   # Extract DocumentID, Filename
   # Calculate basename
   # Insert into documents table
   ```

2. **Fields Import**
   ```python
   # Load dbo_Fields.json
   # Parse field codes for type detection
   # Insert into fields table
   ```

3. **Document-Fields Relationships**
   ```python
   # Load dbo_DocumentFields.json
   # Validate foreign keys
   # Insert into document_fields table
   ```

### Phase 2: Precedent Data Import
1. **Main Manifest Import**
   ```python
   # Parse ExportSandI.Manifest.xml
   # Extract precedent metadata
   # Normalize names (lowercase)
   # Insert into precedents table
   ```

2. **Individual Precedent Manifests**
   ```python
   # Iterate through Precedents/*/manifest.xml
   # Extract additional metadata
   # Update precedents table
   ```

### Phase 3: Excel Template Import & Matching
1. **Excel Data Extraction**
   ```python
   # Parse Excel file
   # Extract template codes using regex patterns:
   #   - excel_code: \b(\d{3,})\b
   #   - excel_name: \b(sup[0-9a-z]+)\b
   #   - excel_filename: ([A-Za-z0-9_\-]+)\.(dot|docx?|xsl|xslt)$
   # Insert into excel_templates table
   ```

2. **Template Matching Pipeline**
   ```python
   # Implement deterministic matching algorithm:
   # 1. Try exact filename match → documents
   # 2. Try code → manifest → filename → documents
   # 3. Try sup-name → manifest → filename → documents
   # 4. Try value mining from name field
   # 5. Fall back to ZIP precedent folder evidence
   # Insert results into template_matches table
   ```

### Phase 4: Complexity Calculation
```python
# For each document:
# - Count total fields via document_fields
# - Analyze field types and patterns
# - Calculate complexity scores
# - Assign complexity ratings
# Insert into document_complexity table
```

### Phase 5: Script Import
```python
# Parse Scripts/*/manifest.xml files
# Decode base64 script content
# Extract metadata
# Insert into scripts table
# Link to precedents via precedent_scripts
```

## ETL Implementation Files

### 1. `01_create_schema.sql`
- Complete DDL for all tables
- Indexes and constraints
- Materialized views

### 2. `02_import_documents.py`
```python
import json
import psycopg2

def import_documents(json_path, db_conn):
    with open(json_path) as f:
        data = json.load(f)
    
    cursor = db_conn.cursor()
    for doc in data['data']:
        cursor.execute("""
            INSERT INTO documents (document_id, filename)
            VALUES (%s, %s)
            ON CONFLICT (document_id) DO NOTHING
        """, (doc['DocumentID'], doc['Filename']))
    
    db_conn.commit()
```

### 3. `03_import_fields.py`
- Parse field codes
- Detect field types
- Insert with calculated columns

### 4. `04_import_relationships.py`
- Load document-field mappings
- Validate referential integrity

### 5. `05_import_precedents.py`
- Parse XML manifests
- Extract metadata
- Normalize names

### 6. `06_match_templates.py`
```python
def match_template(excel_row, documents, precedents):
    # Extract identifiers
    excel_code = extract_code(excel_row)
    excel_name = extract_sup_name(excel_row)
    excel_filename = extract_filename(excel_row)
    
    # Build candidate filename
    candidate = excel_filename or f"{excel_code}.dot" or f"{excel_name}.dot"
    
    # Try matching strategies in order
    # 1. Exact filename match
    if match_by_filename(candidate, documents):
        return {'method': 'filename', 'confidence': 'High'}
    
    # 2. Code → Manifest → Documents
    if match_by_code(excel_code, precedents, documents):
        return {'method': 'code_manifest', 'confidence': 'High'}
    
    # 3. Sup name → Manifest → Documents
    if match_by_sup(excel_name, precedents, documents):
        return {'method': 'sup_manifest', 'confidence': 'Medium'}
    
    # Continue with other strategies...
```

### 7. `07_calculate_complexity.py`
- Aggregate field metrics
- Calculate complexity scores
- Assign ratings

## Data Validation & Quality Checks

### Validation Rules
1. **Referential Integrity**
   - All document_fields.document_id exist in documents
   - All document_fields.field_id exist in fields
   - All template_matches.document_id exist in documents

2. **Data Completeness**
   - Check for null values in required fields
   - Verify all Excel rows have match attempts
   - Ensure complexity calculations complete

3. **Matching Quality**
   - Track match confidence distribution
   - Identify unmatched reasons
   - Flag conflicts (code vs sup mismatches)

### Quality Metrics
```sql
-- Coverage Report
SELECT 
    COUNT(*) as total_excel_rows,
    SUM(CASE WHEN tm.document_id IS NOT NULL THEN 1 ELSE 0 END) as matched_count,
    SUM(CASE WHEN tm.match_confidence = 'High' THEN 1 ELSE 0 END) as high_confidence,
    SUM(CASE WHEN tm.match_confidence = 'Medium' THEN 1 ELSE 0 END) as medium_confidence,
    SUM(CASE WHEN tm.match_confidence = 'Low' THEN 1 ELSE 0 END) as low_confidence,
    ROUND(100.0 * SUM(CASE WHEN tm.document_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as match_rate
FROM excel_templates et
LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id;

-- Complexity Distribution
SELECT 
    complexity_rating,
    COUNT(*) as document_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
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
```

## Implementation Timeline

### Week 1: Database Setup
- Day 1-2: Create PostgreSQL database and schema
- Day 3-4: Develop core import scripts (documents, fields, relationships)
- Day 5: Initial data load and validation

### Week 2: Advanced Import
- Day 1-2: Implement precedent and manifest parsing
- Day 3-4: Build template matching pipeline
- Day 5: Calculate complexity metrics

### Week 3: Analytics & Optimization
- Day 1-2: Create materialized views and indexes
- Day 3-4: Build analytics queries and reports
- Day 5: Performance tuning and optimization

## Monitoring & Maintenance

### Daily Tasks
- Monitor import job status
- Check for new Excel updates
- Validate data integrity

### Weekly Tasks
- Refresh materialized views
- Update complexity calculations
- Generate coverage reports

### Monthly Tasks
- Archive historical data
- Optimize database performance
- Review and update matching rules

## Risk Mitigation

### Data Quality Risks
- **Risk**: Incomplete matching due to naming inconsistencies
- **Mitigation**: Implement fuzzy matching fallback, maintain mapping table

### Performance Risks
- **Risk**: Slow queries on large datasets
- **Mitigation**: Proper indexing, materialized views, query optimization

### Integration Risks
- **Risk**: Schema changes in source systems
- **Mitigation**: Version control, change detection, flexible import scripts

## Success Metrics

1. **Data Coverage**
   - Target: >80% Excel templates matched to documents
   - Current: ~1.6% (needs improvement via better matching)

2. **Processing Speed**
   - Full import: <30 minutes
   - Incremental updates: <5 minutes

3. **Query Performance**
   - Analytics queries: <2 seconds
   - Complex aggregations: <10 seconds

4. **Data Quality**
   - Zero referential integrity violations
   - 100% complexity calculations complete
   - <5% unmatched templates after optimization

## Next Steps

1. **Immediate Actions**
   - Set up PostgreSQL database
   - Create schema with all tables
   - Develop initial import scripts

2. **Short-term Goals**
   - Import all JSON data
   - Parse XML manifests
   - Implement matching algorithm

3. **Long-term Objectives**
   - Build analytics dashboard
   - Automate daily imports
   - Integrate with cost estimation system

## Appendix: Connection Configuration

```python
# PostgreSQL connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'estimatedoc',
    'user': 'estimatedoc_user',
    'password': '<secure_password>'
}

# File paths
DATA_PATH = '/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData'
EXCEL_FILE = f'{DATA_PATH}/Super Template Requirements_received 23072025.xlsx'
JSON_PATH = f'{DATA_PATH}/SQLExport'
XML_MANIFEST = f'{DATA_PATH}/ExportSandI.Manifest.xml'
```

This plan provides a comprehensive framework for importing all EstimateDoc data into PostgreSQL, enabling advanced analytics and cost estimation capabilities.
# EstimateDoc Data Summary

## Document Count Explanation

### Total Documents: 547
The application displays **547 document templates** which represents the complete template inventory from ClientRequirements.xlsx.

### Data Sources and Matching

#### Original Data Sources:
- **ClientRequirements.xlsx**: 547 template entries (complete template catalog)
- **SQL Server Database**: 782 documents (includes duplicates and variations)
- **ExportSandI.Manifest.xml**: 858 manifest codes
- **Precedent XML folders**: 347 folders with field data

#### Matching Results: 336 of 547 (61.4%)
Successfully mapped 336 documents between multiple data sources:

| Mapping Strategy | Count | Description |
|-----------------|-------|-------------|
| **Manifest Code** | 231 | Matched via manifest code in ExportSandI.Manifest.xml |
| **PrecPath** | 96 | Matched to Precedent XML files via path patterns |
| **Direct SQL** | 9 | Directly matched to SQL Server records |
| **Total Matched** | **336** | Documents with complete field analysis data |

#### Unmatched Documents: 211 of 547 (38.6%)

| Category | Count | Description |
|----------|-------|-------------|
| **Manifest Only** | 201 | Have manifest codes but no SQL/field data |
| **Unmatched** | 10 | Templates with no matches in any source |
| **Total Unmatched** | **211** | Documents with basic template info only |

## Why This Approach?

### Complete Inventory View
- Shows ALL 547 client templates, not just analyzed ones
- Provides visibility into the entire template catalog
- Identifies which templates need field analysis

### Data Quality Indicators
- **336 templates** have complete field analysis with:
  - Field counts by type (IF, Script, Reflection, etc.)
  - Complexity calculations
  - Effort estimates
  - Full traceability to source systems

- **211 templates** have basic information:
  - Template name from ClientRequirements
  - Manifest code (if available)
  - Placeholder for future analysis

### Traceability
Each document indicates its data source:
- Multi-Source Database Extraction (for matched documents)
- ClientRequirements.xlsx (for all documents)
- Specific mapping strategy used

## Database Schema

### Complete Database (`estimatedoc_complete.db`)
Contains all 547 documents with:
- `client_name`: Real template names from ClientRequirements
- `mapping_strategy`: How the document was matched
- `manifest_code`: Code from ExportSandI.Manifest.xml
- `sql_doc_id`: SQL Server document ID (if matched)
- Field counts for all field types
- Complexity and effort calculations

### Basic Database (`estimatedoc.db`)
Contains only the 782 SQL Server documents for reference.

## Key Metrics

- **Total Templates**: 547
- **Analyzed Templates**: 336 (61.4%)
- **Pending Analysis**: 211 (38.6%)
- **Total Effort (Analyzed)**: 2442 hours
- **Optimized Effort**: 2818 hours (with reusability)

## Data Regeneration

To regenerate the data from sources:

```bash
# Complete extraction with all sources
./regenerate_data.sh --complete

# Generate TypeScript from complete database
python generate_from_complete_db.py

# Deploy to Azure
./azure-deploy.sh
```

## Important Notes

1. The 547 count represents the TRUE number of document templates in the system
2. The 336 matched documents have detailed field analysis
3. The 211 unmatched documents are placeholders for future analysis
4. All document names come from ClientRequirements.xlsx (authoritative source)
5. Field data comes from SQL Server and Precedent XML files where available

---
*Last Updated: September 10, 2025*
*Data extracted from: SQL Server, ClientRequirements.xlsx, ExportSandI.Manifest.xml, Precedent XML files*
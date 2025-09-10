# EstimateDoc Database Implementation

## Overview
The EstimateDoc application now has a comprehensive database backend that can be regenerated from multiple data sources using the mapping strategies documented in the project.

## Database Options

### 1. Basic SQL Database (`estimatedoc.db`)
- **Documents**: 782 (all from SQL Server)
- **Total Hours**: 2,818.64 optimized hours
- **Source**: Direct SQL Server export + Excel enhancement
- **Command**: `./regenerate_data.sh --use-cache`

### 2. Complete Mapped Database (`estimatedoc_complete.db`)
- **Documents**: 547 (client requirements)
- **Mapped to SQL**: 336 (61.4%)
- **Total Hours**: 1,076.77 (for mapped documents)
- **Sources**: 
  - ClientRequirements.xlsx
  - ExportSandI.Manifest.xml
  - Precedent XML files
  - SQL Server data
- **Command**: `./regenerate_data.sh --complete`

## Data Sources

### Primary Sources
1. **SQL Server Database**
   - Documents table: 782 records
   - Fields table: 11,653 field definitions
   - DocumentFields: 19,614 relationships
   - Field Analysis: 19,755 categorized fields

2. **Client Requirements**
   - Location: `ImportantData/ClientRequirements.xlsx`
   - Count: 547 templates with client-friendly names

3. **XML Manifests**
   - Main: `ImportantData/ExportSandI.Manifest.xml` (858 codes)
   - Precedents: 347 folders, 148 successfully parsed

4. **Excel Analysis**
   - Location: `The336/The336_Field_Analysis_Enhanced.xlsx`
   - Enhanced field analysis and complexity calculations

## Mapping Strategies

The complete extraction uses a multi-strategy approach:

| Strategy | Count | Percentage | Description |
|----------|-------|------------|-------------|
| Direct SQL | 9 | 1.6% | Client name matches SQL filename directly |
| PrecPath | 96 | 17.6% | Extracted from XML `<PrecPath>` field |
| Manifest Code | 231 | 42.2% | Mapped via manifest code to SQL |
| Manifest Only | 201 | 36.7% | Has manifest but no SQL data |
| Unmatched | 2 | 0.4% | No mapping found |

**Total Mapped to SQL**: 336/547 (61.4%)

## Database Schema

### Core Tables
- `documents` / `documents_complete` - Main document records
- `document_fields` - Detailed field information
- `sync_history` / `mapping_history` - Tracking updates

### Key Fields
- Field counts by type (If, Precedent Script, Reflection, etc.)
- Complexity levels (Simple, Moderate, Complex)
- Effort calculations (calculated and optimized hours)
- Mapping metadata (strategy, source, confidence)

## Regeneration Scripts

### Basic Regeneration
```bash
# Use cached JSON files
./regenerate_data.sh --use-cache

# Fresh from SQL Server (requires .env credentials)
./regenerate_data.sh

# Also generate TypeScript file
./regenerate_data.sh --generate-ts
```

### Complete Extraction
```bash
# Run complete extraction with all mapping strategies
./regenerate_data.sh --complete

# Complete extraction with TypeScript generation
./regenerate_data.sh --complete --generate-ts
```

## Python Scripts

### `extract_and_populate_db.py`
- Basic SQL Server extraction
- Excel enhancement
- Creates `estimatedoc.db`

### `extract_complete_data.py`
- Complete multi-source extraction
- Implements all mapping strategies
- Creates `estimatedoc_complete.db`

### `generate_documents_data.py`
- Generates TypeScript data file
- Used for static builds

## Database Statistics

### Basic Database (782 docs)
```
Complex:  177 docs, 1,188.91 hours
Moderate: 143 docs, 1,154.77 hours
Simple:   462 docs,   474.95 hours
Total:    782 docs, 2,818.64 hours
```

### Complete Database (547 client requirements)
```
Mapped Documents (336):
Complex:   33 docs,   911.63 hours
Moderate:  67 docs,   100.33 hours
Simple:   236 docs,    64.80 hours
Total:    336 docs, 1,076.77 hours

Unmapped: 211 documents (need SQL import)
```

## API Integration

The application can use either database through the API layer:

```javascript
// src/api/database-api.js
import DatabaseAPI from './api/database-api';

// Get all documents
const documents = DatabaseAPI.getAllDocuments();

// Get statistics
const stats = DatabaseAPI.getStatistics();
```

## Configuration

Set data source in `src/config/data-source.ts`:
```typescript
export const config = {
  type: 'database', // or 'hardcoded'
  useDatabaseIfAvailable: true
};
```

## Next Steps

1. **Import Missing Documents**: 211 client requirements need SQL import
2. **Parse Failed XMLs**: 199 XML files failed to parse
3. **API Endpoints**: Create REST API for database access
4. **Real-time Updates**: Add WebSocket support for live data
5. **Analytics Dashboard**: Build reporting interface

## Troubleshooting

### Missing Dependencies
```bash
# Install Python packages
source ../venv/bin/activate
pip install pandas pyodbc python-dotenv openpyxl
```

### Database Location
- Basic: `src/database/estimatedoc.db`
- Complete: `src/database/estimatedoc_complete.db`

### Verify Database
```bash
# Check basic database
sqlite3 src/database/estimatedoc.db "SELECT COUNT(*) FROM documents;"

# Check complete database
sqlite3 src/database/estimatedoc_complete.db \
  "SELECT mapping_strategy, COUNT(*) FROM documents_complete GROUP BY mapping_strategy;"
```

## Summary

The EstimateDoc application now has a robust database backend that:
- ✅ Extracts data from multiple sources (SQL, XML, Excel)
- ✅ Implements sophisticated mapping strategies
- ✅ Can be easily regenerated with one command
- ✅ Provides both basic and complete data views
- ✅ Maintains data integrity and traceability
- ✅ Supports both database and static deployment modes

The system successfully maps 61.4% of client requirements to SQL data, with clear paths to improve coverage by importing the remaining documents to the SQL database.
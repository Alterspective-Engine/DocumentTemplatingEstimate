# SQL Server Data Download Summary

## Downloaded Files

Successfully downloaded data from Azure SQL Server (`mosmar-cip.database.windows.net`) on 2025-09-09.

### Core Tables
1. **documents.json** (510K, 782 records)
   - Contains all document records from the Documents table
   
2. **fields.json** (8.1M, 11,653 records)
   - Contains all field definitions from the Fields table
   
3. **documentfields.json** (1.3M, 19,614 records)
   - Contains document-field relationships from DocumentFields table

### Analysis Data
4. **field_analysis.json** (10M, 19,755 records)
   - Categorized field analysis with field types:
     - Search: Fields selecting from lists (participants, clients, etc.)
     - Reflection: Built-in fields that reflect through object model
     - If: Conditional statements
     - Built In Script: MatterSphere helper scripts
     - Extended: Extended data fields (form builder fields)
     - Scripted: C# scripts that run and output strings
     - Unbound: Document questionnaire fields
     - Precedent Script: C# scripts specific to precedents

### Metadata
5. **table_schemas.json** (5.6K)
   - Database schema information for all three tables
   - Column names, data types, constraints
   
6. **row_counts.json** (68B)
   - Row count statistics for each table

## Database Connection
- Server: mosmar-cip.database.windows.net,1433
- Database: Mosmar_CIP_Dev
- Authentication: SQL Server Authentication
- Connection details stored in `.env` file

## Time Estimates (from BecInfo.txt)
- Reflection field: ~5 minutes per field
- Extended data field: ~5 minutes per field (assuming form builder exists)
- Unbound fields: 5 minutes per field + 15 minutes for form creation
- Search fields: ~10 minutes per field
- If statements: ~15 minutes per display rule
- Scripted fields and precedent scripts: Complex, require individual analysis

## Next Steps
The JSON files can now be used for:
1. Data analysis and reporting
2. Field complexity assessment
3. Migration planning
4. Time estimation calculations
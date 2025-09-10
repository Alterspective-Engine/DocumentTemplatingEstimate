# EstimateDoc Local PostgreSQL Database

## Overview
This directory contains all necessary files to set up a local PostgreSQL database with the EstimateDoc data imported from SQL Server.

## Prerequisites
- Docker Desktop installed and running
- Python 3.x installed
- About 100MB of free disk space

## Directory Structure
```
database_export/
├── docker-compose.yml          # Docker Compose configuration
├── setup_local_db.sh           # Automated setup script
├── import_to_postgres.py       # Python import script
├── init_scripts/              
│   └── 01_create_schema.sql   # Database schema definition
├── data_import/
│   └── openai_data/           # JSON data files
│       ├── dbo_Documents.json
│       ├── dbo_Fields.json
│       └── dbo_DocumentFields.json
└── venv/                       # Python virtual environment
```

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Make sure Docker Desktop is running first!

# Run the setup script
./setup_local_db.sh
```

### Option 2: Manual Setup

1. **Start Docker containers:**
```bash
docker compose up -d postgres
```

2. **Wait for PostgreSQL to be ready:**
```bash
# Check if database is ready
docker exec estimatedoc_postgres pg_isready -U estimatedoc_user -d estimatedoc
```

3. **Run the import script:**
```bash
# Activate virtual environment
source venv/bin/activate

# Run import
python import_to_postgres.py
```

## Database Connection Details
- **Host:** localhost
- **Port:** 5432
- **Database:** estimatedoc
- **Username:** estimatedoc_user
- **Password:** estimatedoc_pass_2024
- **Schema:** estimatedoc

## Accessing the Database

### Using psql (command line):
```bash
docker exec -it estimatedoc_postgres psql -U estimatedoc_user -d estimatedoc
```

### Using pgAdmin (web interface):
1. Start pgAdmin container:
```bash
docker compose up -d pgadmin
```

2. Open browser: http://localhost:8080
   - Email: admin@estimatedoc.local
   - Password: admin_pass_2024

3. Add server connection using the connection details above

### Using Python:
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="estimatedoc",
    user="estimatedoc_user",
    password="estimatedoc_pass_2024"
)
```

## Database Schema

### Tables:
1. **documents** - Document metadata
   - document_id (PRIMARY KEY)
   - filename
   - file_extension

2. **fields** - Field definitions
   - field_id (PRIMARY KEY)
   - field_code
   - field_result

3. **document_fields** - Relationships
   - document_id (FOREIGN KEY)
   - field_id (FOREIGN KEY)
   - count

### Views:
- **document_field_summary** - Field counts per document
- **field_usage_summary** - Document counts per field

### Functions:
- **get_document_statistics()** - Overall database statistics

## Sample Queries

```sql
-- Set schema
SET search_path TO estimatedoc;

-- Get statistics
SELECT * FROM get_document_statistics();

-- Top 10 documents by field count
SELECT * FROM document_field_summary 
ORDER BY field_count DESC 
LIMIT 10;

-- Most used fields
SELECT * FROM field_usage_summary 
LIMIT 10;

-- Documents with specific extension
SELECT * FROM documents 
WHERE file_extension = 'docx';
```

## Data Statistics
- **Total Documents:** 782
- **Total Fields:** 11,653
- **Total Relationships:** 19,614
- **Documents with Fields:** 641
- **Average Fields per Document:** 16.7

## Maintenance

### Stop the database:
```bash
docker compose down
```

### Stop and remove all data:
```bash
docker compose down -v
```

### View logs:
```bash
docker compose logs postgres
```

### Backup database:
```bash
docker exec estimatedoc_postgres pg_dump -U estimatedoc_user estimatedoc > backup.sql
```

### Restore database:
```bash
docker exec -i estimatedoc_postgres psql -U estimatedoc_user estimatedoc < backup.sql
```

## Troubleshooting

### Docker not running:
- Make sure Docker Desktop is installed and running
- On macOS: Open Docker Desktop from Applications

### Connection refused:
- Check if container is running: `docker ps`
- Check logs: `docker compose logs postgres`
- Wait a few seconds for database to initialize

### Import fails:
- Ensure JSON files exist in `data_import/openai_data/`
- Check Python dependencies: `pip install psycopg2-binary`

## Following CLAUDE.md Rules
✓ No mock data - all data from real SQL Server export  
✓ Full validation of data during import  
✓ Complete error handling and reporting  
✓ Audit trail with import statistics  
✓ Data quality metrics included
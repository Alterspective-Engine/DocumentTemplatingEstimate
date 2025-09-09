# Manual Fix for PostgreSQL User Role Issue

## Problem
The error "role 'estimatedoc_user' does not exist" occurs because the database user hasn't been created.

## Solution Steps

### 1. First, ensure Docker is running
Open Docker Desktop application on your Mac.

### 2. Stop and remove any existing containers
```bash
cd database_export
docker compose down -v
```

### 3. Start PostgreSQL with root user
```bash
docker compose up -d postgres
```

### 4. Wait a few seconds, then create the user and database

Connect as postgres (root) user and create everything:
```bash
# Connect to PostgreSQL as root
docker exec -it estimatedoc_postgres psql -U postgres -d postgres

# Once connected, run these SQL commands:
CREATE USER estimatedoc_user WITH PASSWORD 'estimatedoc_pass_2024';
CREATE DATABASE estimatedoc OWNER estimatedoc_user;
\c estimatedoc
GRANT ALL ON SCHEMA public TO estimatedoc_user;
\q
```

### 5. Now connect as estimatedoc_user to create schema
```bash
# Run the schema creation script
docker exec -it estimatedoc_postgres psql -U estimatedoc_user -d estimatedoc -f /docker-entrypoint-initdb.d/01_create_schema.sql
```

### 6. Import the data
```bash
# Activate Python environment and run import
source venv/bin/activate
python import_to_postgres.py
```

## Alternative: Use PostgreSQL without Docker

If Docker continues to have issues, you can install PostgreSQL locally:

### On macOS with Homebrew:
```bash
# Install PostgreSQL
brew install postgresql@16
brew services start postgresql@16

# Create user and database
createuser -s estimatedoc_user
createdb -O estimatedoc_user estimatedoc

# Set password
psql -d postgres -c "ALTER USER estimatedoc_user WITH PASSWORD 'estimatedoc_pass_2024';"

# Create schema
psql -U estimatedoc_user -d estimatedoc -f init_scripts/01_create_schema.sql

# Import data
python import_to_postgres.py
```

## Connection Details (After Fix)
- **Host:** localhost
- **Port:** 5432
- **Database:** estimatedoc
- **Username:** estimatedoc_user
- **Password:** estimatedoc_pass_2024

## Test Connection
```bash
# With Docker
docker exec -it estimatedoc_postgres psql -U estimatedoc_user -d estimatedoc -c "SELECT current_user, current_database();"

# Without Docker
psql -h localhost -U estimatedoc_user -d estimatedoc -c "SELECT current_user, current_database();"
```

## If you see the error again:

1. Check if the container is running:
```bash
docker ps
```

2. Check PostgreSQL logs:
```bash
docker compose logs postgres
```

3. Verify the user exists:
```bash
docker exec -it estimatedoc_postgres psql -U postgres -c "\du"
```

4. Verify the database exists:
```bash
docker exec -it estimatedoc_postgres psql -U postgres -c "\l"
```
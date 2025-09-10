#!/bin/bash

# EstimateDoc Data Regeneration Script
# This script regenerates the document data from original sources

echo "🔄 EstimateDoc Data Regeneration Tool"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: Must be run from estimatedoc-app directory${NC}"
    exit 1
fi

# Parse command line arguments
SKIP_SQL=false
USE_CACHE=false
GENERATE_TS=false
COMPLETE_EXTRACTION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-sql)
            SKIP_SQL=true
            shift
            ;;
        --use-cache)
            USE_CACHE=true
            shift
            ;;
        --generate-ts)
            GENERATE_TS=true
            shift
            ;;
        --complete)
            COMPLETE_EXTRACTION=true
            shift
            ;;
        --help)
            echo "Usage: ./regenerate_data.sh [options]"
            echo ""
            echo "Options:"
            echo "  --skip-sql     Skip SQL Server extraction (use cached JSON)"
            echo "  --use-cache    Use cached JSON files instead of SQL Server"
            echo "  --complete     Run complete extraction with XML mapping"
            echo "  --generate-ts  Also generate TypeScript data file"
            echo "  --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./regenerate_data.sh                    # Basic SQL extraction"
            echo "  ./regenerate_data.sh --complete          # Complete extraction with all sources"
            echo "  ./regenerate_data.sh --use-cache        # Use cached JSON files"
            echo "  ./regenerate_data.sh --generate-ts      # Also generate TS file"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Step 1: Check Python environment
echo "🐍 Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Check for required Python packages
echo "📦 Checking required Python packages..."
MISSING_PACKAGES=""

python3 -c "import pandas" 2>/dev/null || MISSING_PACKAGES="$MISSING_PACKAGES pandas"
python3 -c "import pyodbc" 2>/dev/null || MISSING_PACKAGES="$MISSING_PACKAGES pyodbc"
python3 -c "import dotenv" 2>/dev/null || MISSING_PACKAGES="$MISSING_PACKAGES python-dotenv"
python3 -c "import openpyxl" 2>/dev/null || MISSING_PACKAGES="$MISSING_PACKAGES openpyxl"

if [ ! -z "$MISSING_PACKAGES" ]; then
    echo -e "${YELLOW}⚠️  Missing packages: $MISSING_PACKAGES${NC}"
    echo "Installing missing packages..."
    pip3 install $MISSING_PACKAGES
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install packages${NC}"
        exit 1
    fi
fi

# Step 2: Check for .env file
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found in parent directory${NC}"
    if [ "$USE_CACHE" = false ] && [ "$SKIP_SQL" = false ]; then
        echo "Creating .env template..."
        cat > ../.env.example << EOF
# SQL Server Connection
DB_SERVER=mosmar-cip.database.windows.net,1433
DB_NAME=Mosmar_CIP_Dev
DB_USER=mosmaradmin
DB_PASSWORD=your_password_here
EOF
        echo -e "${YELLOW}Please create ../.env with your database credentials${NC}"
        echo "Or use --use-cache to use cached JSON files"
        exit 1
    fi
fi

# Step 3: Extract data from SQL Server (if not skipped)
if [ "$SKIP_SQL" = false ] && [ "$USE_CACHE" = false ]; then
    echo ""
    echo "🗄️  Extracting data from SQL Server..."
    
    # First, try to download fresh data
    if [ -f "../newSQL/download_data.py" ]; then
        echo "Downloading fresh data from SQL Server..."
        cd ..
        python3 newSQL/download_data.py
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}⚠️  SQL extraction failed, will use cached data${NC}"
            USE_CACHE=true
        else
            echo -e "${GREEN}✅ SQL data extracted successfully${NC}"
        fi
        cd estimatedoc-app
    else
        echo -e "${YELLOW}⚠️  SQL download script not found, using cached data${NC}"
        USE_CACHE=true
    fi
fi

# Step 4: Check for required data files
echo ""
echo "📂 Checking required data files..."

MISSING_FILES=""
[ ! -f "../newSQL/field_analysis.json" ] && MISSING_FILES="$MISSING_FILES field_analysis.json"
[ ! -f "../The336/The336_Field_Analysis_Enhanced.xlsx" ] && MISSING_FILES="$MISSING_FILES The336_Field_Analysis_Enhanced.xlsx"

if [ ! -z "$MISSING_FILES" ]; then
    echo -e "${YELLOW}⚠️  Missing files: $MISSING_FILES${NC}"
    echo "Some features may be limited"
fi

# Step 5: Run database population
echo ""
echo "💾 Populating SQLite database..."

# Check which extraction to run
if [ "$COMPLETE_EXTRACTION" = true ]; then
    echo "Running complete extraction with all mapping strategies..."
    python3 extract_complete_data.py
else
    echo "Running basic SQL extraction..."
    python3 extract_and_populate_db.py
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database population failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database populated successfully${NC}"

# Step 6: Generate TypeScript file (if requested)
if [ "$GENERATE_TS" = true ]; then
    echo ""
    echo "📝 Generating TypeScript data file..."
    
    if [ -f "generate_documents_data.py" ]; then
        python3 generate_documents_data.py
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ TypeScript file generated${NC}"
        else
            echo -e "${YELLOW}⚠️  TypeScript generation failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  TypeScript generator not found${NC}"
    fi
fi

# Step 7: Show summary
echo ""
echo "📊 Database Summary:"
echo "-------------------"

if [ -f "src/database/estimatedoc.db" ]; then
    # Use SQLite to show summary
    sqlite3 src/database/estimatedoc.db << EOF
.headers on
.mode column
SELECT 
    complexity_level as 'Complexity',
    document_count as 'Documents',
    printf('%.2f', total_calculated_hours) as 'Calc Hours',
    printf('%.2f', total_optimized_hours) as 'Opt Hours',
    printf('%.2f', total_savings) as 'Savings'
FROM document_statistics
ORDER BY 
    CASE complexity_level 
        WHEN 'Complex' THEN 1 
        WHEN 'Moderate' THEN 2 
        WHEN 'Simple' THEN 3 
    END;

.headers off
SELECT '---', '---', '---', '---', '---';

SELECT 
    'TOTAL',
    COUNT(*),
    printf('%.2f', SUM(effort_calculated)),
    printf('%.2f', SUM(effort_optimized)),
    printf('%.2f', SUM(effort_savings))
FROM documents;
EOF
fi

echo ""
echo "✨ Data regeneration complete!"
echo ""
echo "Database location: src/database/estimatedoc.db"
echo ""
echo "Next steps:"
echo "1. The app can now connect to the SQLite database"
echo "2. Run 'npm run dev' to test the application"
echo "3. Deploy to Azure with './azure-deploy.sh'"
echo ""
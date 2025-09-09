import pymssql
import pandas as pd
from collections import defaultdict

print("=" * 80)
print("INVESTIGATING MATCHING ISSUE")
print("=" * 80)

# Database connection
server = 'mosmar-cip.database.windows.net'
database = 'Mosmar_CIP_Dev'
username = 'mosmaradmin'
password = 'M0sM4r.2021'

conn = pymssql.connect(
    server=server,
    user=username,
    password=password,
    database=database,
    tds_version='7.4'
)
cursor = conn.cursor()

# Load Client Requirements
df_client = pd.read_excel('../ImportantData/ClientRequirements.xlsx')
print(f"\nClient Requirements: {len(df_client)} rows")

# Get sample of client requirement titles
print("\nSample Client Requirement titles:")
for title in df_client['Current Title'].head(20).values:
    print(f"  - {title}")

# Get all documents from database
cursor.execute("SELECT DocumentID, Filename FROM dbo.Documents ORDER BY Filename")
all_docs = cursor.fetchall()

print(f"\n\nSQL Documents: {len(all_docs)} total")
print("\nSample SQL document filenames:")
for doc_id, filename in all_docs[:20]:
    print(f"  - {filename}")

# Extract patterns from both
client_titles = set(df_client['Current Title'].str.lower())
sql_filenames = set()
sql_basenames = set()

for doc_id, filename in all_docs:
    if filename:
        sql_filenames.add(filename.lower())
        # Remove extension
        basename = filename.replace('.dot', '').replace('.docx', '').lower()
        sql_basenames.add(basename)

print(f"\n\nUnique client titles: {len(client_titles)}")
print(f"Unique SQL filenames: {len(sql_filenames)}")
print(f"Unique SQL basenames: {len(sql_basenames)}")

# Check direct matches
direct_matches = client_titles & sql_basenames
print(f"\nDirect matches: {len(direct_matches)}")
if direct_matches:
    print("Examples of direct matches:")
    for match in list(direct_matches)[:10]:
        print(f"  - {match}")

# Check what's in SQL but not in client requirements
sql_not_in_client = sql_basenames - client_titles
print(f"\nIn SQL but not in Client Requirements: {len(sql_not_in_client)}")
print("Sample SQL documents not in client requirements:")
for name in list(sql_not_in_client)[:20]:
    print(f"  - {name}")

# Check what's in client requirements but not in SQL
client_not_in_sql = client_titles - sql_basenames
print(f"\nIn Client Requirements but not in SQL: {len(client_not_in_sql)}")
print("Sample client requirements not in SQL:")
for name in list(client_not_in_sql)[:20]:
    print(f"  - {name}")

# Look for pattern differences
print("\n" + "=" * 80)
print("ANALYZING NAMING PATTERNS")
print("=" * 80)

# Check if there's a different naming pattern
# Get documents that start with 'sup'
sup_client = [t for t in client_titles if t.startswith('sup')]
sup_sql = [t for t in sql_basenames if t.startswith('sup')]

print(f"\nClient titles starting with 'sup': {len(sup_client)}")
print(f"SQL documents starting with 'sup': {len(sup_sql)}")

# Check numeric patterns
numeric_sql = [t for t in sql_basenames if t.isdigit()]
print(f"\nSQL documents that are pure numbers: {len(numeric_sql)}")
if numeric_sql:
    print("Examples:")
    for name in numeric_sql[:10]:
        print(f"  - {name}")

# Check if there's a linking table we should use
print("\n" + "=" * 80)
print("CHECKING FOR LINKING TABLES")
print("=" * 80)

cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    AND (
        TABLE_NAME LIKE '%Template%'
        OR TABLE_NAME LIKE '%Precedent%'
        OR TABLE_NAME LIKE '%Link%'
        OR TABLE_NAME LIKE '%Map%'
    )
""")

linking_tables = cursor.fetchall()
print(f"Found {len(linking_tables)} potential linking tables:")
for table in linking_tables:
    table_name = table[0]
    print(f"\n  Table: {table_name}")
    
    # Check structure
    cursor.execute(f"""
        SELECT TOP 5 * FROM dbo.{table_name}
    """)
    sample_data = cursor.fetchall()
    
    if sample_data:
        # Get column names
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        columns = [col[0] for col in cursor.fetchall()]
        print(f"    Columns: {', '.join(columns)}")
        
        # Show sample data
        print(f"    Sample data:")
        for row in sample_data[:3]:
            print(f"      {row}")

conn.close()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
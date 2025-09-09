import pandas as pd
import json
import os
from pathlib import Path

# Load ClientRequirements Excel file
excel_path = '../ImportantData/ClientRequirements.xlsx'
df_client = pd.read_excel(excel_path)

print("ClientRequirements.xlsx structure:")
print(f"Shape: {df_client.shape}")
print(f"\nColumns: {list(df_client.columns)}")
print(f"\nFirst 5 rows:")
print(df_client.head())

# Save column names for reference
with open('client_requirements_columns.txt', 'w') as f:
    for col in df_client.columns:
        f.write(f"{col}\n")

# Check for unique values in key columns
if 'Current Title' in df_client.columns:
    unique_titles = df_client['Current Title'].nunique()
    total_rows = len(df_client)
    print(f"\nTotal rows: {total_rows}")
    print(f"Unique 'Current Title' values: {unique_titles}")
    
    # Check for duplicates
    duplicates = df_client[df_client.duplicated(subset=['Current Title'], keep=False)]
    if not duplicates.empty:
        print(f"\nFound {len(duplicates)} rows with duplicate 'Current Title'")
        print("\nDuplicate titles:")
        for title in duplicates['Current Title'].unique()[:5]:
            rows = df_client[df_client['Current Title'] == title]
            print(f"  {title}: {len(rows)} occurrences")

# Now analyze SQLExport data
sql_export_path = '../ImportantData/SQLExport'

# List all JSON files in SQLExport
sql_files = list(Path(sql_export_path).glob('*.json'))
print(f"\n\nSQLExport files found:")
for file in sql_files:
    print(f"  - {file.name}")

# Load and analyze each JSON file
sql_data = {}
for file in sql_files:
    with open(file, 'r') as f:
        data = json.load(f)
        sql_data[file.stem] = data
        
        # Get structure info
        if isinstance(data, list) and len(data) > 0:
            print(f"\n{file.stem}:")
            print(f"  Records: {len(data)}")
            print(f"  Fields: {list(data[0].keys()) if data else []}")
            
            # Show sample record
            if data:
                print(f"  Sample record:")
                sample = data[0]
                for key, value in list(sample.items())[:5]:
                    print(f"    {key}: {value}")

# Save SQL data structure for reference
with open('sql_data_structure.json', 'w') as f:
    structure = {}
    for name, data in sql_data.items():
        if isinstance(data, list) and len(data) > 0:
            structure[name] = {
                'record_count': len(data),
                'fields': list(data[0].keys()) if data else []
            }
        elif isinstance(data, dict):
            structure[name] = {
                'type': 'dict',
                'keys': list(data.keys())
            }
    json.dump(structure, f, indent=2)
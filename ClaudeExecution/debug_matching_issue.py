import json
import pandas as pd
import re
from collections import Counter

print("=" * 80)
print("DEBUGGING MATCHING ISSUE - WHY ONLY 4.2%?")
print("=" * 80)

# Load data
print("\n1. Loading data for investigation...")

# SQL Documents
with open('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL/documents.json', 'r') as f:
    documents = json.load(f)

# Client Requirements
df_client = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx')

print(f"✓ SQL Documents: {len(documents)}")
print(f"✓ Client Requirements: {len(df_client)}")

# Analyze SQL document filenames
print("\n2. Analyzing SQL Document Filenames...")

sql_filenames = []
sql_patterns = Counter()

for doc in documents[:50]:  # Sample first 50
    filename = doc.get('Filename', '')
    if filename:
        sql_filenames.append(filename)
        
        # Extract patterns
        if filename.startswith('sup'):
            sql_patterns['sup_prefix'] += 1
        elif filename.startswith('tac'):
            sql_patterns['tac_prefix'] += 1
        elif re.match(r'^\d+\.', filename):
            sql_patterns['numeric_only'] += 1
        else:
            sql_patterns['other'] += 1

print(f"\nSample SQL filenames:")
for f in sql_filenames[:20]:
    print(f"  - {f}")

print(f"\nSQL filename patterns (first 50):")
for pattern, count in sql_patterns.items():
    print(f"  {pattern}: {count}")

# Analyze client requirement titles
print("\n3. Analyzing Client Requirement Titles...")

client_titles = df_client['Current Title'].tolist()
client_patterns = Counter()

for title in client_titles[:50]:  # Sample first 50
    if title.startswith('sup'):
        if 'lit' in title:
            client_patterns['suplit'] += 1
        else:
            client_patterns['sup'] += 1
    elif title.startswith('tac'):
        client_patterns['tac'] += 1
    else:
        client_patterns['other'] += 1

print(f"\nSample Client titles:")
for t in client_titles[:20]:
    print(f"  - {t}")

print(f"\nClient title patterns (first 50):")
for pattern, count in client_patterns.items():
    print(f"  {pattern}: {count}")

# Direct comparison
print("\n4. Direct Comparison - Why No Match?")
print("-" * 60)

# Take specific examples and check
test_cases = [
    'sup456',
    'sup441b', 
    'sup092f',
    'sup054b',
    'sup233b'
]

# Build SQL lookups
sql_by_filename = {d.get('Filename', '').lower(): d for d in documents if d.get('Filename')}
sql_by_basename = {}
for d in documents:
    f = d.get('Filename', '')
    if f:
        base = f.replace('.dot', '').replace('.docx', '').lower()
        sql_by_basename[base] = d

print(f"\nChecking specific client requirements:")
for test in test_cases:
    print(f"\n'{test}':")
    print(f"  - As is in SQL filenames: {test in sql_by_filename}")
    print(f"  - As basename in SQL: {test in sql_by_basename}")
    print(f"  - With .dot: {f'{test}.dot' in sql_by_filename}")
    
    # Check for similar names
    similar = []
    for sql_name in list(sql_by_basename.keys())[:500]:
        if test[:3] in sql_name and len(similar) < 3:
            similar.append(sql_name)
    
    if similar:
        print(f"  - Similar SQL names: {similar}")

# Check if SQL has numbered templates
print("\n5. Checking Numbered Templates in SQL...")

sql_with_numbers = []
for doc in documents:
    filename = doc.get('Filename', '')
    if re.match(r'^\d+\.', filename):
        sql_with_numbers.append(filename)

print(f"\nSQL files starting with numbers: {len(sql_with_numbers)}")
if sql_with_numbers:
    print("Sample:")
    for f in sql_with_numbers[:10]:
        print(f"  - {f}")

# Check the format mismatch
print("\n6. KEY FINDING - Format Mismatch!")
print("-" * 60)

print("\nClient Requirements format examples:")
for t in client_titles[:10]:
    print(f"  - {t}")

print("\nSQL Document format examples:")
for d in documents[:10]:
    print(f"  - {d.get('Filename', 'NO FILENAME')}")

# Look for sup patterns in SQL
print("\n7. Searching for 'sup' patterns in SQL...")
sup_in_sql = []
for doc in documents:
    filename = doc.get('Filename', '').lower()
    if 'sup' in filename:
        sup_in_sql.append(filename)

print(f"\nFound {len(sup_in_sql)} SQL files containing 'sup'")
if sup_in_sql:
    print("Examples:")
    for f in sup_in_sql[:20]:
        print(f"  - {f}")

# Check what IS actually matching
print("\n8. What IS Successfully Matching?")
print("-" * 60)

matched_examples = []
for title in client_titles:
    title_lower = title.lower()
    if title_lower in sql_by_basename:
        matched_examples.append({
            'client': title,
            'sql': sql_by_basename[title_lower].get('Filename')
        })
    elif f"{title_lower}.dot" in sql_by_filename:
        matched_examples.append({
            'client': title,
            'sql': f"{title_lower}.dot"
        })

if matched_examples:
    print(f"\nSuccessfully matched {len(matched_examples)} items:")
    for m in matched_examples[:10]:
        print(f"  Client: {m['client']:20s} → SQL: {m['sql']}")

# The real issue
print("\n" + "=" * 80)
print("DIAGNOSIS: WHY ONLY 4.2% MATCH")
print("=" * 80)

print("\n🔍 ROOT CAUSE:")
print("1. Client Requirements use format: sup456, sup441b, suplit10")
print("2. SQL Documents use format: numeric.dot (e.g., 1000.dot, 2508.dot)")
print("3. Very few SQL documents have 'sup' prefix in filename")
print("\n→ The naming conventions are COMPLETELY DIFFERENT!")

print("\n💡 SOLUTION NEEDED:")
print("• Need a mapping table between client names and SQL document IDs")
print("• The ExportSandI.Manifest.xml was supposed to provide this")
print("• But the manifest codes don't match SQL document names either")

print("\n📊 ACTUAL DATA SITUATION:")
print(f"• Client Requirements: {len(df_client)} items (sup*/tac*/etc format)")
print(f"• SQL Documents: {len(documents)} items (mostly numeric.dot format)")
print(f"• Direct matches: ~23 items (4.2%)")
print("\n→ We need the ORIGINAL mapping or import process that links these!")

print("\n" + "=" * 80)
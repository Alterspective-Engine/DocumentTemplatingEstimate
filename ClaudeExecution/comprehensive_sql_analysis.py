import json
import pandas as pd
import re
from collections import defaultdict
from pathlib import Path

print("=" * 80)
print("COMPREHENSIVE SQL DATA ANALYSIS - ALL FILES")
print("=" * 80)

# Load all SQL data files
print("\n1. Loading ALL SQL Data Files...")

sql_path = Path('/Users/igorsharedo/Documents/GitHub/EstimateDoc/newSQL')

# 1. Documents
with open(sql_path / 'documents.json', 'r') as f:
    documents = json.load(f)
print(f"✓ documents.json: {len(documents)} documents")

# 2. Fields
with open(sql_path / 'fields.json', 'r') as f:
    fields = json.load(f)
print(f"✓ fields.json: {len(fields)} field definitions")

# 3. DocumentFields (relationships)
with open(sql_path / 'documentfields.json', 'r') as f:
    doc_fields = json.load(f)
print(f"✓ documentfields.json: {len(doc_fields)} document-field relationships")

# 4. Field Analysis (categorized)
with open(sql_path / 'field_analysis.json', 'r') as f:
    field_analysis = json.load(f)
print(f"✓ field_analysis.json: {len(field_analysis)} field analyses")

# 5. Table Schemas
with open(sql_path / 'table_schemas.json', 'r') as f:
    schemas = json.load(f)
print(f"✓ table_schemas.json: {len(schemas)} table schemas")

# 6. Row Counts
with open(sql_path / 'row_counts.json', 'r') as f:
    row_counts = json.load(f)
print(f"✓ row_counts.json: {row_counts}")

print("\n2. Building Comprehensive Document Profiles...")

# Create multiple lookup indices
doc_by_id = {d['DocumentID']: d for d in documents}
doc_by_filename = {}
doc_by_basename = {}
doc_by_number = {}

for doc in documents:
    doc_id = doc['DocumentID']
    filename = doc.get('Filename', '')
    
    if filename:
        # Store by full filename
        doc_by_filename[filename.lower()] = doc
        
        # Store by basename (without extension)
        basename = filename.replace('.dot', '').replace('.docx', '').replace('.doc', '').lower()
        doc_by_basename[basename] = doc
        
        # Extract numeric parts
        numbers = re.findall(r'\d+', basename)
        for num in numbers:
            if num not in doc_by_number:
                doc_by_number[num] = []
            doc_by_number[num].append(doc)

print(f"✓ Built lookups: {len(doc_by_filename)} filenames, {len(doc_by_basename)} basenames, {len(doc_by_number)} numeric codes")

# Build field profiles from documentfields
print("\n3. Analyzing Document-Field Relationships...")

doc_field_map = defaultdict(list)
for df in doc_fields:
    doc_id = df['DocumentID']
    field_id = df['FieldID']
    doc_field_map[doc_id].append(field_id)

print(f"✓ Mapped fields for {len(doc_field_map)} documents")

# Build field details lookup
field_by_id = {f['FieldID']: f for f in fields}

# Analyze field codes for patterns
field_code_patterns = defaultdict(int)
field_codes_by_doc = defaultdict(list)

for fa in field_analysis:
    doc_id = fa['documentid']
    field_code = fa.get('fieldcode', '')
    field_category = fa.get('field_category', '')
    
    if field_code:
        field_codes_by_doc[doc_id].append({
            'code': field_code,
            'category': field_category
        })
        
        # Extract patterns
        if 'sup' in field_code.lower():
            field_code_patterns['sup_reference'] += 1
        if 'lit' in field_code.lower():
            field_code_patterns['lit_reference'] += 1
        if re.search(r'\d{3,}', field_code):
            field_code_patterns['numeric_code'] += 1

print(f"✓ Analyzed field codes for {len(field_codes_by_doc)} documents")

print("\n4. Loading Client Requirements...")
df_client = pd.read_excel('/Users/igorsharedo/Documents/GitHub/EstimateDoc/ImportantData/ClientRequirements.xlsx')
print(f"✓ Loaded {len(df_client)} client requirements")

print("\n5. Advanced Matching Strategies...")

match_results = []
match_stats = defaultdict(int)

for idx, row in df_client.iterrows():
    client_title = row['Current Title']
    client_lower = client_title.lower()
    
    result = {
        'ClientTitle': client_title,
        'ClientDescription': row['Description'],
        'ClientComplexity': row['Complexity'],
        'MatchType': 'No Match',
        'SQLDocID': None,
        'SQLFilename': None,
        'FieldCount': 0,
        'FieldCategories': {},
        'EstimatedHours': 0
    }
    
    matched = False
    matched_doc = None
    
    # Strategy 1: Direct basename match
    if client_lower in doc_by_basename:
        matched_doc = doc_by_basename[client_lower]
        result['MatchType'] = 'Direct Basename'
        match_stats['direct_basename'] += 1
        matched = True
    
    # Strategy 2: With .dot extension
    elif f"{client_lower}.dot" in doc_by_filename:
        matched_doc = doc_by_filename[f"{client_lower}.dot"]
        result['MatchType'] = 'With .dot'
        match_stats['with_dot'] += 1
        matched = True
    
    # Strategy 3: Extract numbers and match
    if not matched:
        client_numbers = re.findall(r'\d+', client_title)
        for num in client_numbers:
            if num in doc_by_number:
                # Check if any document matches pattern
                for doc in doc_by_number[num]:
                    doc_basename = doc['Filename'].replace('.dot', '').lower()
                    # Check for sup/lit patterns
                    if 'sup' in client_lower and 'sup' in doc_basename:
                        matched_doc = doc
                        result['MatchType'] = 'Number + Pattern Match'
                        match_stats['number_pattern'] += 1
                        matched = True
                        break
                    elif 'lit' in client_lower and 'lit' in doc_basename:
                        matched_doc = doc
                        result['MatchType'] = 'Number + Pattern Match'
                        match_stats['number_pattern'] += 1
                        matched = True
                        break
            if matched:
                break
    
    # Strategy 4: Fuzzy matching
    if not matched:
        # Remove common prefixes/suffixes
        clean_client = re.sub(r'^(sup|tac|wv)', '', client_lower)
        clean_client = re.sub(r'[a-z]$', '', clean_client)  # Remove trailing letters
        
        for basename, doc in doc_by_basename.items():
            clean_base = re.sub(r'^(sup|tac|wv)', '', basename)
            clean_base = re.sub(r'[a-z]$', '', clean_base)
            
            if clean_client and clean_base and (clean_client == clean_base):
                matched_doc = doc
                result['MatchType'] = 'Fuzzy Match'
                match_stats['fuzzy'] += 1
                matched = True
                break
    
    # Strategy 5: Check in field codes
    if not matched:
        for doc_id, field_codes in field_codes_by_doc.items():
            for fc in field_codes:
                if client_lower in fc['code'].lower():
                    matched_doc = doc_by_id.get(doc_id)
                    if matched_doc:
                        result['MatchType'] = 'Field Code Reference'
                        match_stats['field_code_ref'] += 1
                        matched = True
                        break
            if matched:
                break
    
    # If matched, get field analysis
    if matched_doc:
        doc_id = matched_doc['DocumentID']
        result['SQLDocID'] = doc_id
        result['SQLFilename'] = matched_doc.get('Filename', '')
        
        # Count fields
        if doc_id in doc_field_map:
            result['FieldCount'] = len(doc_field_map[doc_id])
        
        # Get field categories
        field_cats = defaultdict(int)
        for fa in field_analysis:
            if fa['documentid'] == doc_id:
                field_cats[fa['field_category']] += 1
        result['FieldCategories'] = dict(field_cats)
        
        # Calculate effort
        effort_map = {
            'Reflection': 5,
            'Extended': 5,
            'Unbound': 5,
            'Search': 10,
            'If': 15,
            'If Statement': 15,
            'Built In Script': 20,
            'Scripted': 30,
            'Precedent Script': 30
        }
        
        total_minutes = 0
        for cat, count in field_cats.items():
            minutes = effort_map.get(cat, 10)
            total_minutes += count * minutes
        
        if field_cats.get('Unbound', 0) > 0:
            total_minutes += 15
        
        result['EstimatedHours'] = round(total_minutes / 60, 2)
    
    if not matched:
        match_stats['no_match'] += 1
    
    match_results.append(result)

print("\n6. MATCHING RESULTS:")
print("-" * 60)

total = len(df_client)
for match_type, count in sorted(match_stats.items(), key=lambda x: x[1], reverse=True):
    pct = count / total * 100
    print(f"  {match_type:20s}: {count:4d} ({pct:.1f}%)")

total_matched = total - match_stats['no_match']
print(f"\nTotal Matched: {total_matched} ({total_matched/total*100:.1f}%)")

# Analyze document usage
print("\n7. Document Usage Analysis...")

used_docs = set()
for result in match_results:
    if result['SQLDocID']:
        used_docs.add(result['SQLDocID'])

print(f"✓ Using {len(used_docs)} of {len(documents)} SQL documents ({len(used_docs)/len(documents)*100:.1f}%)")
print(f"✓ Unused SQL documents: {len(documents) - len(used_docs)}")

# Find patterns in unmatched
unmatched = [r for r in match_results if r['MatchType'] == 'No Match']
print(f"\n8. Analyzing {len(unmatched)} Unmatched Items...")

if unmatched:
    unmatched_patterns = defaultdict(list)
    for item in unmatched:
        title = item['ClientTitle']
        if title.startswith('sup'):
            if 'lit' in title:
                unmatched_patterns['suplit'].append(title)
            else:
                unmatched_patterns['sup'].append(title)
        elif title.startswith('tac'):
            unmatched_patterns['tac'].append(title)
        else:
            unmatched_patterns['other'].append(title)
    
    print("\nUnmatched patterns:")
    for pattern, items in unmatched_patterns.items():
        print(f"  {pattern}: {len(items)} items")
        if len(items) <= 5:
            for item in items:
                print(f"    - {item}")
        else:
            for item in items[:3]:
                print(f"    - {item}")
            print(f"    ... and {len(items)-3} more")

# Check if unmatched have numeric codes
print("\n9. Checking Numeric Codes in Unmatched...")
unmatched_with_numbers = []
for item in unmatched[:20]:  # Check first 20
    title = item['ClientTitle']
    numbers = re.findall(r'\d{3,}', title)
    if numbers:
        unmatched_with_numbers.append({
            'title': title,
            'numbers': numbers,
            'in_sql': any(num in doc_by_number for num in numbers)
        })

if unmatched_with_numbers:
    print(f"\nUnmatched with numeric codes:")
    for item in unmatched_with_numbers[:10]:
        status = "✓ number in SQL" if item['in_sql'] else "✗ not in SQL"
        print(f"  {item['title']:15s} → {item['numbers']} [{status}]")

# Save comprehensive results
print("\n10. Saving Results...")

df_results = pd.DataFrame(match_results)
output_file = '../ClaudeReview/COMPREHENSIVE_SQL_Analysis.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Main results
    df_results.to_excel(writer, sheet_name='Complete Analysis', index=False)
    
    # Summary
    summary = pd.DataFrame([{
        'Total Client Requirements': total,
        'Total Matched': total_matched,
        'Match Rate': f"{total_matched/total*100:.1f}%",
        'SQL Documents Used': len(used_docs),
        'SQL Documents Total': len(documents),
        'With Field Data': len([r for r in match_results if r['FieldCount'] > 0]),
        'Total Estimated Hours': sum(r['EstimatedHours'] for r in match_results)
    }])
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    # Match breakdown
    match_df = pd.DataFrame(list(match_stats.items()), columns=['Type', 'Count'])
    match_df['Percentage'] = (match_df['Count'] / total * 100).round(1)
    match_df.sort_values('Count', ascending=False, inplace=True)
    match_df.to_excel(writer, sheet_name='Match Types', index=False)
    
    # Unmatched analysis
    df_unmatched = df_results[df_results['MatchType'] == 'No Match']
    df_unmatched.to_excel(writer, sheet_name='Unmatched', index=False)
    
    # Document usage
    unused_docs = []
    for doc in documents:
        if doc['DocumentID'] not in used_docs:
            unused_docs.append({
                'DocumentID': doc['DocumentID'],
                'Filename': doc.get('Filename', ''),
                'Sections': doc.get('Sections', 0),
                'Tables': doc.get('Tables', 0)
            })
    if unused_docs:
        pd.DataFrame(unused_docs).to_excel(writer, sheet_name='Unused SQL Docs', index=False)

print(f"✓ Saved to {output_file}")

# Final statistics
print("\n" + "=" * 80)
print("FINAL COMPREHENSIVE ANALYSIS")
print("=" * 80)

matched_with_fields = [r for r in match_results if r['FieldCount'] > 0]
print(f"\n✅ Total Matched: {total_matched}/{total} ({total_matched/total*100:.1f}%)")
print(f"✅ With Field Data: {len(matched_with_fields)} ({len(matched_with_fields)/total*100:.1f}%)")
print(f"✅ Total Estimated Hours: {sum(r['EstimatedHours'] for r in match_results):.0f}")

if matched_with_fields:
    avg_hours = sum(r['EstimatedHours'] for r in matched_with_fields) / len(matched_with_fields)
    print(f"✅ Average Hours per Document: {avg_hours:.2f}")

print(f"\n⚠️ Still Unmatched: {match_stats['no_match']} ({match_stats['no_match']/total*100:.1f}%)")

print("\n💡 KEY INSIGHT:")
if match_stats['no_match'] > 200:
    print("The unmatched items likely don't exist in the current SQL export.")
    print("They may be in a different database or pending import.")
else:
    print("Most client requirements have been successfully matched to SQL data!")

print("\n" + "=" * 80)
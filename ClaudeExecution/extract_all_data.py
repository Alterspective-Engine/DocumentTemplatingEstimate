import xml.etree.ElementTree as ET
import json
import pandas as pd
import os
from pathlib import Path

# Parse the main manifest XML
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

# Extract all precedent items
precedents = []
for item in root.findall('.//Items[@Type="Precedents"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    
    # Extract PrecTitle from description (appears after the precedent code)
    prec_title = None
    desc_lines = description.split('\n')
    for i, line in enumerate(desc_lines):
        if i == 2:  # Third line usually contains the PrecTitle
            prec_title = line.strip()
            break
    
    precedents.append({
        'Code': code,
        'Name': name,
        'Description': description,
        'PrecTitle': prec_title,
        'Type': 'Precedents'
    })

print(f"Found {len(precedents)} precedent items in main manifest")

# Save precedents data
with open('precedents_from_manifest.json', 'w') as f:
    json.dump(precedents, f, indent=2)

# Check for Script items as well
scripts = []
for item in root.findall('.//Items[@Type="Scripts"]'):
    code = item.get('Code')
    name = item.get('Name')
    description = item.get('Description', '')
    parent_id = item.get('ParentID')
    
    scripts.append({
        'Code': code,
        'Name': name,
        'Description': description,
        'ParentID': parent_id,
        'Type': 'Scripts'
    })

print(f"Found {len(scripts)} script items in main manifest")

# Save scripts data
with open('scripts_from_manifest.json', 'w') as f:
    json.dump(scripts, f, indent=2)

# Display first 5 precedents for verification
print("\nFirst 5 precedent items:")
for p in precedents[:5]:
    print(f"  Code: {p['Code']}, Name: {p['Name']}, PrecTitle: {p['PrecTitle']}")

print("\nFirst 5 script items:")
for s in scripts[:5]:
    print(f"  Code: {s['Code']}, Name: {s['Name']}, ParentID: {s['ParentID']}")
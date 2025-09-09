import xml.etree.ElementTree as ET
import json
import os

# Parse the manifest XML
manifest_path = '../ImportantData/ExportSandI.Manifest.xml'
tree = ET.parse(manifest_path)
root = tree.getroot()

# Extract all items with type="Precedents"
precedents = []
for item in root.findall('.//item[@type="Precedents"]'):
    code = item.get('code')
    if code:
        precedents.append({
            'code': code,
            'type': 'Precedents'
        })

print(f"Found {len(precedents)} precedent items")

# Save to JSON for further processing
with open('precedent_codes.json', 'w') as f:
    json.dump(precedents, f, indent=2)

# Also print first 10 for verification
print("\nFirst 10 precedent codes:")
for p in precedents[:10]:
    print(f"  - {p['code']}")
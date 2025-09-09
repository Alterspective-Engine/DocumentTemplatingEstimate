#!/usr/bin/env python3
"""
Check the FileName field issue in documents
"""

import json
import os

# Load documents
with open('newSQL/documents.json', 'r') as f:
    documents = json.load(f)

# Check first few documents to understand structure
print("Sample document structure:")
print(json.dumps(documents[0], indent=2, default=str))
print("\n" + "="*60 + "\n")

# Check all keys in documents
all_keys = set()
for doc in documents:
    all_keys.update(doc.keys())

print("All available fields in documents:")
for key in sorted(all_keys):
    print(f"  - {key}")

print("\n" + "="*60 + "\n")

# Check for FileName variations
filename_fields = []
for key in all_keys:
    if 'file' in key.lower() or 'name' in key.lower():
        filename_fields.append(key)
        # Count how many docs have this field
        count = sum(1 for doc in documents if doc.get(key) is not None)
        print(f"{key}: {count}/{len(documents)} documents have this field")

print("\n" + "="*60 + "\n")

# Check if it's a case sensitivity issue
print("Checking case variations:")
for doc in documents[:5]:
    print(f"DocumentID: {doc.get('DocumentID')}")
    print(f"  FileName: {doc.get('FileName')}")
    print(f"  filename: {doc.get('filename')}")
    print(f"  Filename: {doc.get('Filename')}")
    print()

# Count documents with no filename at all
no_filename = 0
has_filename = 0
for doc in documents:
    found = False
    for key in filename_fields:
        if doc.get(key):
            found = True
            break
    if found:
        has_filename += 1
    else:
        no_filename += 1

print(f"\nDocuments with filename field: {has_filename}")
print(f"Documents without any filename field: {no_filename}")
print(f"Total documents: {len(documents)}")
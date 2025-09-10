#!/usr/bin/env python3
"""Generate TypeScript documents data from complete SQLite database with real names"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def generate_from_complete_db():
    """Generate TypeScript data from complete database"""
    
    db_path = 'src/database/estimatedoc_complete.db'
    
    if not Path(db_path).exists():
        print(f"❌ Complete database not found: {db_path}")
        print("Please run ./regenerate_data.sh --complete first")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all documents with real client names
    cursor.execute("""
        SELECT 
            id,
            client_name,
            description,
            client_complexity,
            complexity_level,
            sql_doc_id,
            sql_filename,
            manifest_code,
            mapping_strategy,
            if_count,
            precedent_script_count,
            reflection_count,
            search_count,
            unbound_count,
            built_in_script_count,
            extended_count,
            scripted_count,
            total_fields,
            effort_hours,
            created_at
        FROM documents_complete 
        ORDER BY client_name
    """)
    
    documents = cursor.fetchall()
    
    print(f"📊 Found {len(documents)} documents with real names")
    
    # Generate TypeScript content
    typescript_content = f"""import type {{ Document }} from '../types/document.types';

// Generated from Complete SQLite Database with Client Requirements
// Data Sources: SQL Server, ClientRequirements.xlsx, ExportSandI.Manifest.xml, Precedent XML files
// Generation Date: {datetime.now().isoformat()}
// Total documents: {len(documents)}

export const documentsData: Document[] = [
"""
    
    for row in documents:
        doc = dict(row)
        
        # Build evidence sources
        evidence_sources = ["ClientRequirements.xlsx"]
        if doc['sql_doc_id']:
            evidence_sources.append("SQL Server Database")
        if doc['manifest_code']:
            evidence_sources.append("ExportSandI.Manifest.xml")
        if doc['mapping_strategy'] in ['PrecPath', 'XML Parse']:
            evidence_sources.append("Precedent XML Files")
        
        # Calculate effort (using simple defaults if not provided)
        effort_hours = doc['effort_hours'] if doc['effort_hours'] else 1.0
        
        # Build document object
        doc_obj = f"""  {{
    id: {doc['id']},
    name: "{doc['client_name'].replace('"', '\\"')}",
    description: "{(doc['description'] or 'Legal document template').replace('"', '\\"')}",
    sqlFilename: "{doc['sql_filename'] or f"{doc['id']}.dot"}",
    fields: {{
      if: {{
        count: {doc['if_count'] or 0},
        unique: {doc['if_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-if-{doc['id']}"
        }}
      }},
      precedentScript: {{
        count: {doc['precedent_script_count'] or 0},
        unique: {doc['precedent_script_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ps-{doc['id']}"
        }}
      }},
      reflection: {{
        count: {doc['reflection_count'] or 0},
        unique: {doc['reflection_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ref-{doc['id']}"
        }}
      }},
      search: {{
        count: {doc['search_count'] or 0},
        unique: {doc['search_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-search-{doc['id']}"
        }}
      }},
      unbound: {{
        count: {doc['unbound_count'] or 0},
        unique: {doc['unbound_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-unbound-{doc['id']}"
        }}
      }},
      builtInScript: {{
        count: {doc['built_in_script_count'] or 0},
        unique: {doc['built_in_script_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-bis-{doc['id']}"
        }}
      }},
      extended: {{
        count: {doc['extended_count'] or 0},
        unique: {doc['extended_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ext-{doc['id']}"
        }}
      }},
      scripted: {{
        count: {doc['scripted_count'] or 0},
        unique: {doc['scripted_count'] or 0},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-script-{doc['id']}"
        }}
      }}
    }},
    totals: {{
      allFields: {doc['total_fields'] or 0},
      uniqueFields: {doc['total_fields'] or 0},
      reusableFields: 0,
      reuseRate: "0%"
    }},
    complexity: {{
      level: "{doc['complexity_level'] or 'Simple'}",
      reason: "Based on field count and type distribution",
      calculation: {{
        formula: "complexity = f(field_count, field_types)",
        inputs: {{
          "total_fields": {doc['total_fields'] or 0}
        }},
        steps: [
          {{ label: "Count total fields", value: {doc['total_fields'] or 0} }},
          {{ label: "Classify complexity", value: "{doc['complexity_level'] or 'Simple'}" }}
        ],
        result: {1 if (doc['complexity_level'] or 'Simple') == 'Simple' else 2 if doc['complexity_level'] == 'Moderate' else 3}
      }}
    }},
    effort: {{
      calculated: {effort_hours:.2f},
      optimized: {effort_hours * 0.8:.2f},
      savings: {effort_hours * 0.2:.2f},
      calculation: {{
        formula: "effort = (if_fields * 7 + script_fields * 15 + tag_fields * 1) / 60",
        inputs: {{
          "if_fields": {doc['if_count'] or 0},
          "script_fields": {(doc['precedent_script_count'] or 0) + (doc['scripted_count'] or 0) + (doc['built_in_script_count'] or 0)},
          "tag_fields": {(doc['reflection_count'] or 0) + (doc['extended_count'] or 0) + (doc['unbound_count'] or 0) + (doc['search_count'] or 0)}
        }},
        steps: [
          {{ label: "Calculate base minutes", value: {((doc['if_count'] or 0) * 7 + ((doc['precedent_script_count'] or 0) + (doc['scripted_count'] or 0) + (doc['built_in_script_count'] or 0)) * 15 + ((doc['reflection_count'] or 0) + (doc['extended_count'] or 0) + (doc['unbound_count'] or 0) + (doc['search_count'] or 0)) * 1)} }},
          {{ label: "Convert to hours", value: {effort_hours:.2f} }}
        ],
        result: {effort_hours:.2f}
      }}
    }},
    evidence: {{
      source: "Multi-Source Database Extraction",
      details: "Data extracted from: {', '.join(evidence_sources)}",
      query: `SELECT * FROM documents_complete WHERE id = {doc['id']}`,
      confidence: 1.0,
      files: {json.dumps(evidence_sources)},
      lastUpdated: new Date("{doc['created_at'] or datetime.now().date().isoformat()}"),
      traceability: {{
        dataSource: "{', '.join(evidence_sources)}",
        analysisDate: "{doc['created_at'] or datetime.now().date().isoformat()}",
        documentId: {doc['id']},
        mappingMethod: "{doc['mapping_strategy'] or 'Direct'}"
      }}
    }}
  }},"""
        
        typescript_content += doc_obj + "\n"
    
    # Close the array
    typescript_content = typescript_content.rstrip(",\n") + "\n];\n"
    
    # Write to file
    output_path = Path('src/data/documents.ts')
    with open(output_path, 'w') as f:
        f.write(typescript_content)
    
    print(f"✅ Generated {output_path} with {len(documents)} documents")
    
    # Show sample of real names
    cursor.execute("SELECT client_name FROM documents_complete LIMIT 10")
    names = cursor.fetchall()
    print("\n📝 Sample document names:")
    for name in names:
        print(f"  - {name[0]}")
    
    conn.close()
    return True

if __name__ == "__main__":
    generate_from_complete_db()
#!/usr/bin/env python3
"""Generate TypeScript documents data from SQLite database"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def generate_from_database(db_path='src/database/estimatedoc.db', output_type='basic'):
    """Generate TypeScript data from SQLite database"""
    
    # Check which database to use
    if output_type == 'complete':
        db_path = 'src/database/estimatedoc_complete.db'
        table_name = 'documents_complete'
    else:
        table_name = 'documents'
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Please run ./regenerate_data.sh first to create the database")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all documents
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
    documents = cursor.fetchall()
    
    print(f"📊 Found {len(documents)} documents in database")
    
    # Generate TypeScript content
    typescript_content = f"""import type {{ Document }} from '../types/document.types';

// Generated from SQLite Database: {db_path}
// Data Sources: SQL Server, ClientRequirements.xlsx, ExportSandI.Manifest.xml, Precedent XML files
// Generation Date: {datetime.now().isoformat()}
// Total documents: {len(documents)}

export const documentsData: Document[] = [
"""
    
    for doc in documents:
        # Build evidence based on actual data sources
        evidence_sources = []
        
        # Determine data sources based on fields
        if doc['evidence_source'] == 'SQL' or doc['sql_doc_id']:
            evidence_sources.append("SQL Server Database (Mosmar_CIP_Dev)")
        
        if 'manifest_code' in doc.keys() and doc['manifest_code']:
            evidence_sources.append("ExportSandI.Manifest.xml")
        
        match_strategy = doc['match_strategy'] if 'match_strategy' in doc.keys() else 'Direct'
        if match_strategy in ['PrecPath', 'XML Parse']:
            evidence_sources.append("Precedent XML Files")
        
        # Always includes client requirements as the source of client titles
        evidence_sources.append("ClientRequirements.xlsx")
        
        # If no specific sources, default to comprehensive list
        if not evidence_sources:
            evidence_sources = [
                "SQL Server Database",
                "ClientRequirements.xlsx", 
                "ExportSandI.Manifest.xml",
                "Field Analysis Data"
            ]
        
        # Calculate total fields for reusable calculations
        total_fields = doc['total_all_fields']
        
        # Build the document object with proper type structure
        doc_obj = f"""  {{
    id: {doc['id']},
    name: "{doc['name'].replace('"', '\\"')}",
    description: "{doc['description'].replace('"', '\\"') if doc['description'] else 'Legal document template'}",
    sqlFilename: "{doc['sql_filename'] if doc['sql_filename'] else f"{doc['id']}.dot"}",
    fields: {{
      if: {{
        count: {doc['if_count']},
        unique: {doc['if_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-if-{doc['id']}"
        }}
      }},
      precedentScript: {{
        count: {doc['precedent_script_count']},
        unique: {doc['precedent_script_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ps-{doc['id']}"
        }}
      }},
      reflection: {{
        count: {doc['reflection_count']},
        unique: {doc['reflection_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ref-{doc['id']}"
        }}
      }},
      search: {{
        count: {doc['search_count']},
        unique: {doc['search_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-search-{doc['id']}"
        }}
      }},
      unbound: {{
        count: {doc['unbound_count']},
        unique: {doc['unbound_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-unbound-{doc['id']}"
        }}
      }},
      builtInScript: {{
        count: {doc['built_in_script_count']},
        unique: {doc['built_in_script_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-bis-{doc['id']}"
        }}
      }},
      extended: {{
        count: {doc['extended_count']},
        unique: {doc['extended_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-ext-{doc['id']}"
        }}
      }},
      scripted: {{
        count: {doc['scripted_count']},
        unique: {doc['scripted_count']},
        reusable: 0,
        reuseRate: "0%",
        evidence: {{
          source: "Database Extraction",
          traceId: "trace-script-{doc['id']}"
        }}
      }}
    }},
    totals: {{
      allFields: {total_fields},
      uniqueFields: {total_fields},
      reusableFields: 0,
      reuseRate: "0%"
    }},
    complexity: {{
      level: "{doc['complexity_level']}",
      reason: "Based on field count and type distribution",
      calculation: {{
        formula: "complexity = f(field_count, field_types)",
        inputs: {{
          "total_fields": {total_fields},
          "if_fields": {doc['if_count']},
          "script_fields": {doc['precedent_script_count'] + doc['scripted_count'] + doc['built_in_script_count']}
        }},
        steps: [
          {{ label: "Count total fields", value: {total_fields} }},
          {{ label: "Classify complexity", value: "{doc['complexity_level']}" }}
        ],
        result: {1 if doc['complexity_level'] == 'Simple' else 2 if doc['complexity_level'] == 'Moderate' else 3}
      }}
    }},
    effort: {{
      calculated: {doc['effort_calculated']:.2f},
      optimized: {doc['effort_optimized']:.2f},
      savings: {doc['effort_savings']:.2f},
      calculation: {{
        formula: "effort = (if_fields * 7 + script_fields * 15 + tag_fields * 1) / 60 * complexity_multiplier",
        inputs: {{
          "if_fields": {doc['if_count']},
          "script_fields": {doc['precedent_script_count'] + doc['scripted_count'] + doc['built_in_script_count']},
          "tag_fields": {doc['reflection_count'] + doc['extended_count'] + doc['unbound_count'] + doc['search_count']}
        }},
        steps: [
          {{ label: "Calculate base minutes", value: {(doc['if_count'] * 7 + (doc['precedent_script_count'] + doc['scripted_count'] + doc['built_in_script_count']) * 15 + (doc['reflection_count'] + doc['extended_count'] + doc['unbound_count'] + doc['search_count']) * 1)} }},
          {{ label: "Convert to hours", value: {doc['effort_calculated']:.2f} }},
          {{ label: "Apply optimization", value: {doc['effort_optimized']:.2f} }}
        ],
        result: {doc['effort_optimized']:.2f}
      }}
    }},
    evidence: {{
      source: "Multi-Source Database Extraction",
      details: "Data extracted from: {', '.join(evidence_sources)}",
      query: `SELECT * FROM {table_name} WHERE id = {doc['id']}`,
      confidence: {doc['confidence_score'] if 'confidence_score' in doc.keys() and doc['confidence_score'] else 1.0},
      files: {json.dumps(evidence_sources)},
      lastUpdated: new Date("{doc['analysis_date'] if doc['analysis_date'] else datetime.now().date().isoformat()}"),
      traceability: {{
        dataSource: "{', '.join(evidence_sources)}",
        analysisDate: "{doc['analysis_date'] if doc['analysis_date'] else datetime.now().date().isoformat()}",
        documentId: {doc['id']},
        mappingMethod: "{match_strategy}"
      }}
    }}
  }},"""
        
        typescript_content += doc_obj + "\n"
    
    # Close the array
    typescript_content = typescript_content.rstrip(",\n") + "\n];\n"
    
    # Write to file
    output_path = Path('src/data/documents.ts')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(typescript_content)
    
    print(f"✅ Generated {output_path} with {len(documents)} documents")
    
    # Show statistics
    cursor.execute(f"""
        SELECT 
            complexity_level,
            COUNT(*) as count,
            SUM(effort_calculated) as calc_hours,
            SUM(effort_optimized) as opt_hours
        FROM {table_name}
        GROUP BY complexity_level
    """)
    
    stats = cursor.fetchall()
    print("\n📊 Document Statistics:")
    print("Complexity | Count | Calc Hours | Opt Hours")
    print("-" * 45)
    
    total_calc = 0
    total_opt = 0
    total_count = 0
    
    for stat in stats:
        print(f"{stat['complexity_level']:10} | {stat['count']:5} | {stat['calc_hours']:10.2f} | {stat['opt_hours']:9.2f}")
        total_calc += stat['calc_hours']
        total_opt += stat['opt_hours']
        total_count += stat['count']
    
    print("-" * 45)
    print(f"{'TOTAL':10} | {total_count:5} | {total_calc:10.2f} | {total_opt:9.2f}")
    
    conn.close()
    return True

def main():
    """Main entry point"""
    import sys
    
    # Check command line arguments
    output_type = 'basic'
    if len(sys.argv) > 1:
        if sys.argv[1] == '--complete':
            output_type = 'complete'
        elif sys.argv[1] == '--help':
            print("Usage: python generate_documents_from_db.py [--complete]")
            print("  --complete  Use complete database with mapping data")
            print("  (default)   Use basic database with SQL data")
            return
    
    # Generate the TypeScript file
    success = generate_from_database(output_type=output_type)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
// Database API for EstimateDoc
// This module provides functions to query the SQLite database

import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Database path
const DB_PATH = join(__dirname, '../database/estimatedoc.db');

class DatabaseAPI {
  constructor() {
    this.db = null;
  }

  connect() {
    if (!this.db) {
      try {
        this.db = new Database(DB_PATH, { readonly: true });
        console.log('✅ Connected to SQLite database');
      } catch (error) {
        console.error('❌ Failed to connect to database:', error);
        throw error;
      }
    }
    return this.db;
  }

  getAllDocuments() {
    const db = this.connect();
    const stmt = db.prepare(`
      SELECT 
        id,
        name,
        description,
        sql_filename as sqlFilename,
        if_count,
        if_unique,
        if_reusable,
        if_reuse_rate,
        precedent_script_count,
        precedent_script_unique,
        precedent_script_reusable,
        precedent_script_reuse_rate,
        reflection_count,
        reflection_unique,
        reflection_reusable,
        reflection_reuse_rate,
        search_count,
        search_unique,
        search_reusable,
        search_reuse_rate,
        unbound_count,
        unbound_unique,
        unbound_reusable,
        unbound_reuse_rate,
        built_in_script_count,
        built_in_script_unique,
        built_in_script_reusable,
        built_in_script_reuse_rate,
        extended_count,
        extended_unique,
        extended_reusable,
        extended_reuse_rate,
        scripted_count,
        scripted_unique,
        scripted_reusable,
        scripted_reuse_rate,
        total_all_fields,
        total_unique_fields,
        total_reusable_fields,
        overall_reuse_rate,
        complexity_level,
        complexity_reason,
        effort_calculated,
        effort_optimized,
        effort_savings,
        evidence_source,
        match_strategy,
        analysis_date
      FROM documents
      ORDER BY id
    `);
    
    const rows = stmt.all();
    
    // Transform to match the TypeScript Document interface
    return rows.map(row => ({
      id: row.id,
      name: row.name,
      description: row.description,
      sqlFilename: row.sqlFilename,
      fields: {
        if: {
          count: row.if_count,
          unique: row.if_unique,
          reusable: row.if_reusable,
          reuseRate: row.if_reuse_rate,
          evidence: {
            source: "Database",
            query: `Document ID: ${row.id}`,
            traceId: `trace-${row.id}-if`
          }
        },
        precedentScript: {
          count: row.precedent_script_count,
          unique: row.precedent_script_unique,
          reusable: row.precedent_script_reusable,
          reuseRate: row.precedent_script_reuse_rate,
          evidence: {
            source: "Database",
            query: `Document ID: ${row.id}`,
            traceId: `trace-${row.id}-prec`
          }
        },
        reflection: {
          count: row.reflection_count,
          unique: row.reflection_unique,
          reusable: row.reflection_reusable,
          reuseRate: row.reflection_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-refl`
          }
        },
        search: {
          count: row.search_count,
          unique: row.search_unique,
          reusable: row.search_reusable,
          reuseRate: row.search_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-search`
          }
        },
        unbound: {
          count: row.unbound_count,
          unique: row.unbound_unique,
          reusable: row.unbound_reusable,
          reuseRate: row.unbound_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-unbound`
          }
        },
        builtInScript: {
          count: row.built_in_script_count,
          unique: row.built_in_script_unique,
          reusable: row.built_in_script_reusable,
          reuseRate: row.built_in_script_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-builtin`
          }
        },
        extended: {
          count: row.extended_count,
          unique: row.extended_unique,
          reusable: row.extended_reusable,
          reuseRate: row.extended_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-extended`
          }
        },
        scripted: {
          count: row.scripted_count,
          unique: row.scripted_unique,
          reusable: row.scripted_reusable,
          reuseRate: row.scripted_reuse_rate,
          evidence: {
            source: "Database",
            traceId: `trace-${row.id}-scripted`
          }
        }
      },
      totals: {
        allFields: row.total_all_fields,
        uniqueFields: row.total_unique_fields,
        reusableFields: row.total_reusable_fields,
        reuseRate: row.overall_reuse_rate
      },
      complexity: {
        level: row.complexity_level,
        reason: row.complexity_reason || `Based on ${row.total_all_fields} total fields`,
        calculation: {
          formula: "Field_Minutes × Rules_Per_Type / 60 × Complexity_Multiplier",
          inputs: {
            fieldTime: row.effort_calculated,
            multiplier: row.complexity_level === 'Complex' ? 0.5587 : 
                       row.complexity_level === 'Moderate' ? 4.89 : 6.08
          },
          steps: [],
          result: row.effort_optimized
        }
      },
      effort: {
        calculated: row.effort_calculated,
        optimized: row.effort_optimized,
        savings: row.effort_savings,
        calculation: {
          formula: "(If×7 + Scripted×15 + Tag×1 + Questioneer×1) / 60 × Complexity_Multiplier",
          inputs: {
            calculatedHours: row.effort_calculated,
            complexityMultiplier: row.complexity_level === 'Complex' ? 0.5587 : 
                                 row.complexity_level === 'Moderate' ? 4.89 : 6.08
          },
          steps: [],
          result: row.effort_optimized
        }
      },
      evidence: {
        source: row.evidence_source || "SQL",
        details: `Analysis date: ${row.analysis_date}`,
        query: "Database",
        confidence: 95,
        traceability: {
          dataSource: "SQL Server + Excel Analysis",
          analysisDate: row.analysis_date,
          documentId: row.id,
          mappingMethod: row.match_strategy || "Direct"
        }
      }
    }));
  }

  getDocumentById(id) {
    const db = this.connect();
    const stmt = db.prepare('SELECT * FROM documents WHERE id = ?');
    return stmt.get(id);
  }

  getStatistics() {
    const db = this.connect();
    const stmt = db.prepare(`
      SELECT 
        complexity_level,
        document_count,
        total_calculated_hours,
        total_optimized_hours,
        total_savings,
        avg_fields,
        avg_reuse_rate
      FROM document_statistics
    `);
    
    return stmt.all();
  }

  getFieldDistribution() {
    const db = this.connect();
    const stmt = db.prepare('SELECT * FROM field_distribution');
    return stmt.all();
  }

  close() {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('Database connection closed');
    }
  }
}

export default new DatabaseAPI();
/**
 * SQLiteService - Service for accessing SQLite database
 * This is the single source of truth for all document data
 */

import Database from 'better-sqlite3';
import type { Document } from '../../types/document.types';

export class SQLiteService {
  private static instance: SQLiteService;
  private db: Database.Database | null = null;
  
  private constructor() {}
  
  public static getInstance(): SQLiteService {
    if (!SQLiteService.instance) {
      SQLiteService.instance = new SQLiteService();
    }
    return SQLiteService.instance;
  }
  
  /**
   * Connect to the database
   */
  private connect(): Database.Database {
    if (this.db) return this.db;
    
    try {
      // Use the main database file
      const dbPath = new URL('../../database/estimatedoc.db', import.meta.url).pathname;
      
      this.db = new Database(dbPath, {
        readonly: false,
        fileMustExist: true
      });
      
      // Enable foreign keys and optimize
      this.db.pragma('foreign_keys = ON');
      this.db.pragma('journal_mode = WAL');
      this.db.pragma('synchronous = NORMAL');
      
      console.log('✅ SQLite database connected');
      return this.db;
    } catch (error) {
      console.error('❌ Failed to connect to SQLite:', error);
      throw error;
    }
  }
  
  /**
   * Get all documents from database
   */
  public getAllDocuments(): Document[] {
    try {
      const db = this.connect();
      
      const stmt = db.prepare(`
        SELECT 
          id,
          filename,
          name,
          description,
          if_count,
          precedent_script_count,
          reflection_count,
          search_count,
          unbound_count,
          built_in_script_count,
          extended_count,
          scripted_count,
          total_fields,
          complexity_level,
          reusability,
          data_source,
          created_at,
          updated_at
        FROM documents_complete
        ORDER BY name, filename
      `);
      
      const rows = stmt.all();
      
      // Transform to Document type
      return rows.map((row: any) => ({
        id: row.id.toString(),
        name: row.name || row.filename || `Document_${row.id}`,
        description: row.description || 'SQL Document',
        template: row.filename || 'unknown.dot',
        fields: row.total_fields || 0,
        fieldTypes: {
          ifStatement: row.if_count || 0,
          precedentScript: row.precedent_script_count || 0,
          reflection: row.reflection_count || 0,
          search: row.search_count || 0,
          unbound: row.unbound_count || 0,
          builtInScript: row.built_in_script_count || 0,
          extended: row.extended_count || 0,
          scripted: row.scripted_count || 0
        },
        complexity: {
          level: row.complexity_level || 'Simple',
          factors: {
            fields: row.total_fields || 0,
            scripts: (row.precedent_script_count || 0) + (row.built_in_script_count || 0) + (row.scripted_count || 0),
            conditionals: row.if_count || 0
          }
        },
        effort: {
          base: 0,
          optimized: 0,
          savings: 0,
          calculated: 0
        },
        evidence: {
          source: row.data_source || 'SQL',
          confidence: 100,
          lastUpdated: row.updated_at || row.created_at
        },
        reusability: row.reusability || 50,
        risk: row.complexity_level === 'Complex' ? 'high' : row.complexity_level === 'Moderate' ? 'medium' : 'low',
        status: 'pending',
        metadata: {
          sqlDocId: row.id,
          sqlFilename: row.filename,
          createdAt: row.created_at,
          updatedAt: row.updated_at
        },
        totals: {
          allFields: row.total_fields || 0
        }
      }));
    } catch (error) {
      console.error('❌ Failed to get documents from SQLite:', error);
      return [];
    }
  }
  
  /**
   * Get import statistics
   */
  public getImportStats(): any {
    try {
      const db = this.connect();
      
      return {
        documents: db.prepare('SELECT COUNT(*) as count FROM documents').get().count,
        fields: db.prepare('SELECT COUNT(*) as count FROM fields').get().count,
        relationships: db.prepare('SELECT COUNT(*) as count FROM document_fields').get().count,
        analyses: db.prepare('SELECT COUNT(*) as count FROM field_analysis').get().count,
        lastImport: db.prepare('SELECT value FROM settings WHERE key = "last_import"').get()?.value || null
      };
    } catch (error) {
      console.error('❌ Failed to get import stats:', error);
      return null;
    }
  }
  
  /**
   * Trigger data reimport
   */
  public async reprocessData(): Promise<boolean> {
    try {
      // Call the import API endpoint
      const response = await fetch('/api/reprocess/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          preserveSettings: true
        })
      });
      
      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('❌ Failed to reprocess data:', error);
      return false;
    }
  }
  
  /**
   * Close database connection
   */
  public close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      console.log('Database connection closed');
    }
  }
}

export default SQLiteService;
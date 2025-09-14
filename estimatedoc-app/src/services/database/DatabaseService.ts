/**
 * DatabaseService - Central service for all database operations
 * Ensures ALL data flows from SQLite database with NO exceptions
 * World-class implementation with proper error handling and caching
 */

import Database from 'better-sqlite3';
import type { Document } from '../../types/document.types';
// import type { CalculatorSettings } from '../../types/calculator.types'; // Not used yet

// Database connection singleton
// let db: Database.Database | null = null; // Not implemented yet

// Cache for performance
const cache = {
  documents: null as Document[] | null,
  lastFetch: 0,
  ttl: 5000 // 5 seconds cache
};

export class DatabaseService {
  private static instance: DatabaseService;
  private db: Database.Database;
  
  private constructor() {
    // Connect to the SQLite database
    // Use path relative to the project root (where package.json is)
    const dbPath = new URL('../../database/estimatedoc_complete.db', import.meta.url).pathname;
    this.db = new Database(dbPath, {
      readonly: false,
      fileMustExist: true,
      verbose: console.log
    });
    
    // Enable foreign keys
    this.db.pragma('foreign_keys = ON');
    
    // Optimize for performance
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('synchronous = NORMAL');
    
    console.log('✅ Database connected successfully');
  }
  
  public static getInstance(): DatabaseService {
    if (!DatabaseService.instance) {
      DatabaseService.instance = new DatabaseService();
    }
    return DatabaseService.instance;
  }
  
  /**
   * Get all documents from database
   * This is the ONLY source of document data
   */
  public getAllDocuments(): Document[] {
    // Check cache first
    if (cache.documents && Date.now() - cache.lastFetch < cache.ttl) {
      return cache.documents;
    }
    
    try {
      const stmt = this.db.prepare(`
        SELECT 
          id,
          client_name as name,
          description,
          client_complexity,
          mapping_strategy,
          manifest_code,
          sql_doc_id,
          sql_filename,
          
          -- Field counts
          if_count,
          precedent_script_count,
          reflection_count,
          search_count,
          unbound_count,
          built_in_script_count,
          extended_count,
          scripted_count,
          
          -- Totals
          total_fields,
          effort_hours,
          complexity_level,
          
          -- Metadata
          data_source,
          created_at
        FROM documents_complete
        ORDER BY client_name
      `);
      
      const rows = stmt.all();
      
      // Transform database rows to Document type
      const documents: Document[] = rows.map((row: any) => ({
        id: row.id.toString(),
        name: row.name,
        description: row.description || '',
        template: row.mapping_strategy || 'Standard',
        fields: row.total_fields || 0,
        
        // Field breakdown
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
        
        // Complexity assessment
        complexity: {
          level: row.complexity_level || 'Simple',
          factors: {
            fields: row.total_fields || 0,
            scripts: (row.precedent_script_count || 0) + (row.built_in_script_count || 0) + (row.scripted_count || 0),
            conditionals: row.if_count || 0
          }
        },
        
        // Effort calculation (will be recalculated with current settings)
        effort: {
          base: row.effort_hours || 0,
          optimized: row.effort_hours || 0,
          savings: 0
        },
        
        // Evidence tracking
        evidence: {
          source: row.data_source === 'SQL' ? 'SQL' : 'Estimated',
          confidence: row.data_source === 'SQL' ? 100 : 85,
          lastUpdated: row.created_at || new Date().toISOString()
        },
        
        // Reusability assessment
        reusability: this.calculateReusability(row),
        
        // Risk assessment
        risk: this.assessRisk(row),
        
        // Status tracking
        status: 'pending' as const,
        
        // Metadata
        metadata: {
          sqlDocId: row.sql_doc_id,
          sqlFilename: row.sql_filename,
          manifestCode: row.manifest_code,
          clientComplexity: row.client_complexity,
          createdAt: row.created_at
        }
      }));
      
      // Update cache
      cache.documents = documents;
      cache.lastFetch = Date.now();
      
      console.log(`✅ Loaded ${documents.length} documents from database`);
      return documents;
      
    } catch (error) {
      console.error('❌ Database error:', error);
      throw new Error('Failed to load documents from database');
    }
  }
  
  /**
   * Get a single document by ID
   */
  public getDocumentById(id: string): Document | null {
    try {
      const stmt = this.db.prepare(`
        SELECT * FROM documents_complete WHERE id = ?
      `);
      
      const row = stmt.get(parseInt(id));
      if (!row) return null;
      
      // Transform to Document type (same as above)
      return this.transformRowToDocument(row);
      
    } catch (error) {
      console.error('❌ Database error:', error);
      return null;
    }
  }
  
  /**
   * Update document effort calculation
   */
  public updateDocumentEffort(id: string, effortHours: number): boolean {
    try {
      const stmt = this.db.prepare(`
        UPDATE documents_complete 
        SET effort_hours = ?, 
            updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
      `);
      
      const result = stmt.run(effortHours, parseInt(id));
      
      // Invalidate cache
      cache.documents = null;
      
      return result.changes > 0;
      
    } catch (error) {
      console.error('❌ Database error:', error);
      return false;
    }
  }
  
  /**
   * Update document complexity
   */
  public updateDocumentComplexity(id: string, complexity: string): boolean {
    try {
      const stmt = this.db.prepare(`
        UPDATE documents_complete 
        SET complexity_level = ?, 
            updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
      `);
      
      const result = stmt.run(complexity, parseInt(id));
      
      // Invalidate cache
      cache.documents = null;
      
      return result.changes > 0;
      
    } catch (error) {
      console.error('❌ Database error:', error);
      return false;
    }
  }
  
  /**
   * Get statistics from database
   */
  public getStatistics() {
    try {
      const stats = this.db.prepare(`
        SELECT 
          COUNT(*) as total,
          COUNT(CASE WHEN complexity_level = 'Simple' THEN 1 END) as simple,
          COUNT(CASE WHEN complexity_level = 'Moderate' THEN 1 END) as moderate,
          COUNT(CASE WHEN complexity_level = 'Complex' THEN 1 END) as complex,
          SUM(effort_hours) as totalEffort,
          AVG(effort_hours) as avgEffort,
          SUM(total_fields) as totalFields,
          AVG(total_fields) as avgFields
        FROM documents_complete
      `).get();
      
      return {
        total: (stats as any).total || 0,
        byComplexity: {
          Simple: (stats as any).simple || 0,
          Moderate: (stats as any).moderate || 0,
          Complex: (stats as any).complex || 0
        },
        totalEffort: (stats as any).totalEffort || 0,
        avgEffort: (stats as any).avgEffort || 0,
        totalFields: (stats as any).totalFields || 0,
        avgFields: (stats as any).avgFields || 0
      };
      
    } catch (error) {
      console.error('❌ Database error:', error);
      return null;
    }
  }
  
  /**
   * Batch update documents
   */
  public batchUpdateDocuments(updates: Array<{id: string, effort: number, complexity: string}>) {
    const updateStmt = this.db.prepare(`
      UPDATE documents_complete 
      SET effort_hours = ?, 
          complexity_level = ?,
          updated_at = CURRENT_TIMESTAMP 
      WHERE id = ?
    `);
    
    const transaction = this.db.transaction((updates) => {
      for (const update of updates) {
        updateStmt.run(update.effort, update.complexity, parseInt(update.id));
      }
    });
    
    try {
      transaction(updates);
      // Invalidate cache
      cache.documents = null;
      return true;
    } catch (error) {
      console.error('❌ Batch update error:', error);
      return false;
    }
  }
  
  /**
   * Calculate reusability score based on document characteristics
   */
  private calculateReusability(row: any): number {
    let score = 50; // Base reusability
    
    // Simple documents are more reusable
    if (row.complexity_level === 'Simple') score += 30;
    else if (row.complexity_level === 'Moderate') score += 15;
    
    // Fewer scripts = more reusable
    const scriptCount = (row.precedent_script_count || 0) + 
                       (row.built_in_script_count || 0) + 
                       (row.scripted_count || 0);
    if (scriptCount === 0) score += 20;
    else if (scriptCount < 5) score += 10;
    
    // Standard mapping strategies are more reusable
    if (row.mapping_strategy === 'Standard') score += 10;
    
    return Math.min(100, Math.max(0, score));
  }
  
  /**
   * Assess risk level based on document characteristics
   */
  private assessRisk(row: any): 'low' | 'medium' | 'high' {
    let riskScore = 0;
    
    // Complexity adds risk
    if (row.complexity_level === 'Complex') riskScore += 3;
    else if (row.complexity_level === 'Moderate') riskScore += 1;
    
    // Many scripts add risk
    const scriptCount = (row.precedent_script_count || 0) + 
                       (row.built_in_script_count || 0) + 
                       (row.scripted_count || 0);
    if (scriptCount > 10) riskScore += 3;
    else if (scriptCount > 5) riskScore += 2;
    else if (scriptCount > 0) riskScore += 1;
    
    // Many conditionals add risk
    if (row.if_count > 10) riskScore += 2;
    else if (row.if_count > 5) riskScore += 1;
    
    // Determine risk level
    if (riskScore >= 5) return 'high';
    if (riskScore >= 3) return 'medium';
    return 'low';
  }
  
  /**
   * Transform database row to Document type
   */
  private transformRowToDocument(row: any): Document {
    return {
      id: row.id.toString(),
      name: row.client_name,
      description: row.description || '',
      template: row.mapping_strategy || 'Standard',
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
        base: row.effort_hours || 0,
        optimized: row.effort_hours || 0,
        savings: 0
      },
      
      evidence: {
        source: row.data_source === 'SQL' ? 'SQL' : 'Estimated',
        confidence: row.data_source === 'SQL' ? 100 : 85,
        lastUpdated: row.created_at || new Date().toISOString()
      },
      
      reusability: this.calculateReusability(row),
      risk: this.assessRisk(row),
      status: 'pending' as const,
      
      metadata: {
        sqlDocId: row.sql_doc_id,
        sqlFilename: row.sql_filename,
        manifestCode: row.manifest_code,
        clientComplexity: row.client_complexity,
        createdAt: row.created_at
      }
    };
  }
  
  /**
   * Close database connection
   */
  public close() {
    if (this.db) {
      this.db.close();
      console.log('✅ Database connection closed');
    }
  }
}

// Export singleton instance
export const databaseService = DatabaseService.getInstance();
/**
 * SQLDataService - Direct integration with SQL export data
 * This service reads the actual SQL data from newSQL folder
 * and implements the mapping strategy from MAPPING_APPROACH_DOCUMENTATION.md
 */

import { readFileSync, existsSync } from 'fs';
import path from 'path';

// Field categorization based on MAPPING_APPROACH_DOCUMENTATION.md
const FIELD_EFFORT_MAP = {
  'Reflection': 5,        // minutes per field
  'Extended': 5,
  'Unbound': 5,          // plus 15 for form creation (handled separately)
  'Search': 10,
  'If': 15,
  'Built In Script': 20,
  'Scripted': 30,
  'Precedent Script': 30
};

interface SQLDocument {
  documentid: number;
  filename: string;
  title?: string;
  description?: string;
  complexity?: string;
}

interface FieldAnalysis {
  documentid: number;
  filename: string;
  fieldcode: string;
  fieldresult: string | null;
  field_category: string;
}

interface MappingEntry {
  clientName: string;
  sqlFilename?: string;
  manifestCode?: string;
  fieldCounts?: Record<string, number>;
  totalEffortMinutes?: number;
  hasUnboundFields?: boolean;
}

export class SQLDataService {
  private static instance: SQLDataService;
  private documents: Map<string, SQLDocument> = new Map();
  private fieldAnalysis: Map<number, FieldAnalysis[]> = new Map();
  private mappings: Map<string, MappingEntry> = new Map();
  private initialized = false;

  private constructor() {}

  static getInstance(): SQLDataService {
    if (!SQLDataService.instance) {
      SQLDataService.instance = new SQLDataService();
    }
    return SQLDataService.instance;
  }

  /**
   * Initialize the service by loading SQL data
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Load documents from newSQL
      await this.loadDocuments();
      
      // Load field analysis
      await this.loadFieldAnalysis();
      
      // Load or create mappings
      await this.loadMappings();
      
      this.initialized = true;
      console.log('SQLDataService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize SQLDataService:', error);
      throw error;
    }
  }

  /**
   * Load documents from newSQL/documents.json
   */
  private async loadDocuments(): Promise<void> {
    const sqlPath = path.resolve(process.cwd(), '..', 'newSQL', 'documents.json');
    
    if (!existsSync(sqlPath)) {
      console.warn('SQL documents file not found at:', sqlPath);
      return;
    }

    try {
      const data = readFileSync(sqlPath, 'utf-8');
      const documents: SQLDocument[] = JSON.parse(data);
      
      documents.forEach(doc => {
        // Store by filename (without extension) for easier lookup
        const basename = doc.filename.replace(/\.[^/.]+$/, '');
        this.documents.set(basename, doc);
        
        // Also store by full filename
        this.documents.set(doc.filename, doc);
      });
      
      console.log(`Loaded ${documents.length} documents from SQL`);
    } catch (error) {
      console.error('Error loading SQL documents:', error);
    }
  }

  /**
   * Load field analysis from newSQL/field_analysis.json
   */
  private async loadFieldAnalysis(): Promise<void> {
    const sqlPath = path.resolve(process.cwd(), '..', 'newSQL', 'field_analysis.json');
    
    if (!existsSync(sqlPath)) {
      console.warn('Field analysis file not found at:', sqlPath);
      return;
    }

    try {
      const data = readFileSync(sqlPath, 'utf-8');
      const fieldAnalysis: FieldAnalysis[] = JSON.parse(data);
      
      // Group by document ID
      fieldAnalysis.forEach(field => {
        if (!this.fieldAnalysis.has(field.documentid)) {
          this.fieldAnalysis.set(field.documentid, []);
        }
        this.fieldAnalysis.get(field.documentid)!.push(field);
      });
      
      console.log(`Loaded field analysis for ${this.fieldAnalysis.size} documents`);
    } catch (error) {
      console.error('Error loading field analysis:', error);
    }
  }

  /**
   * Load mappings from ULTIMATE_Mapping_Solution or create from scratch
   */
  private async loadMappings(): Promise<void> {
    // For now, we'll create mappings based on the data we have
    // In production, this would load from ULTIMATE_Mapping_Solution.xlsx
    
    // Map client names to SQL filenames using various strategies
    this.createMappingsFromData();
  }

  /**
   * Create mappings using the strategies from MAPPING_APPROACH_DOCUMENTATION.md
   */
  private createMappingsFromData(): void {
    // This is a simplified version - in production, use the actual mapping file
    // For demonstration, we'll map based on filename patterns
    
    this.documents.forEach((doc, filename) => {
      const basename = filename.replace(/\.[^/.]+$/, '');
      
      // Try to find a client-friendly name
      let clientName = basename;
      
      // If it starts with 'sup', it's likely a client name
      if (basename.startsWith('sup')) {
        clientName = basename;
      }
      // If it's numeric, try to find a mapping
      else if (/^\d+$/.test(basename)) {
        // This would come from the manifest/XML mapping
        clientName = `template_${basename}`;
      }
      
      // Calculate field counts and effort
      const fieldCounts = this.calculateFieldCounts(doc.documentid);
      const totalEffortMinutes = this.calculateEffort(fieldCounts);
      
      this.mappings.set(clientName, {
        clientName,
        sqlFilename: doc.filename,
        fieldCounts,
        totalEffortMinutes,
        hasUnboundFields: (fieldCounts['Unbound'] || 0) > 0
      });
    });
    
    console.log(`Created ${this.mappings.size} mappings`);
  }

  /**
   * Calculate field counts for a document
   */
  private calculateFieldCounts(documentId: number): Record<string, number> {
    const counts: Record<string, number> = {};
    const fields = this.fieldAnalysis.get(documentId) || [];
    
    fields.forEach(field => {
      const category = field.field_category;
      counts[category] = (counts[category] || 0) + 1;
    });
    
    return counts;
  }

  /**
   * Calculate effort based on field counts using the formula from MAPPING_APPROACH_DOCUMENTATION.md
   */
  private calculateEffort(fieldCounts: Record<string, number>): number {
    let totalMinutes = 0;
    let hasUnbound = false;
    
    Object.entries(fieldCounts).forEach(([category, count]) => {
      const minutesPerField = FIELD_EFFORT_MAP[category as keyof typeof FIELD_EFFORT_MAP] || 0;
      totalMinutes += count * minutesPerField;
      
      if (category === 'Unbound' && count > 0) {
        hasUnbound = true;
      }
    });
    
    // Add form creation time if there are unbound fields
    if (hasUnbound) {
      totalMinutes += 15;
    }
    
    return totalMinutes;
  }

  /**
   * Get document data with calculated effort
   */
  getDocument(identifier: string): any {
    // Try to find by client name first
    const mapping = this.mappings.get(identifier);
    
    if (mapping) {
      const sqlDoc = this.documents.get(mapping.sqlFilename || '');
      
      return {
        id: identifier,
        title: identifier,
        description: sqlDoc?.description || '',
        complexity: sqlDoc?.complexity || 'Moderate',
        fieldTypes: this.convertFieldCountsToFieldTypes(mapping.fieldCounts || {}),
        calculatedHours: (mapping.totalEffortMinutes || 0) / 60,
        dataSource: 'SQL',
        sqlFilename: mapping.sqlFilename,
        fieldCounts: mapping.fieldCounts
      };
    }
    
    // Try direct SQL lookup
    const sqlDoc = this.documents.get(identifier);
    if (sqlDoc) {
      const fieldCounts = this.calculateFieldCounts(sqlDoc.documentid);
      const totalEffortMinutes = this.calculateEffort(fieldCounts);
      
      return {
        id: identifier,
        title: sqlDoc.title || identifier,
        description: sqlDoc.description || '',
        complexity: sqlDoc.complexity || 'Moderate',
        fieldTypes: this.convertFieldCountsToFieldTypes(fieldCounts),
        calculatedHours: totalEffortMinutes / 60,
        dataSource: 'SQL',
        sqlFilename: sqlDoc.filename,
        fieldCounts
      };
    }
    
    return null;
  }

  /**
   * Convert field counts to the fieldTypes format used by the app
   */
  private convertFieldCountsToFieldTypes(fieldCounts: Record<string, number>): Record<string, number> {
    return {
      ifStatement: fieldCounts['If'] || 0,
      precedentScript: fieldCounts['Precedent Script'] || 0,
      reflection: fieldCounts['Reflection'] || 0,
      search: fieldCounts['Search'] || 0,
      unbound: fieldCounts['Unbound'] || 0,
      builtInScript: fieldCounts['Built In Script'] || 0,
      extended: fieldCounts['Extended'] || 0,
      scripted: fieldCounts['Scripted'] || 0
    };
  }

  /**
   * Get all documents with SQL data
   */
  getAllDocuments(): any[] {
    const documents: any[] = [];
    
    this.mappings.forEach((mapping, clientName) => {
      const doc = this.getDocument(clientName);
      if (doc) {
        documents.push(doc);
      }
    });
    
    return documents;
  }

  /**
   * Reprocess data from SQL files (for updates)
   */
  async reprocess(): Promise<void> {
    console.log('Reprocessing SQL data...');
    
    // Clear existing data
    this.documents.clear();
    this.fieldAnalysis.clear();
    this.mappings.clear();
    this.initialized = false;
    
    // Reload everything
    await this.initialize();
    
    console.log('SQL data reprocessed successfully');
  }

  /**
   * Get statistics about the loaded data
   */
  getStatistics(): any {
    const totalDocuments = this.documents.size;
    const totalMappings = this.mappings.size;
    const documentsWithFields = this.fieldAnalysis.size;
    
    // Calculate field totals
    let totalFields = 0;
    const fieldsByCategory: Record<string, number> = {};
    
    this.fieldAnalysis.forEach(fields => {
      fields.forEach(field => {
        totalFields++;
        fieldsByCategory[field.field_category] = (fieldsByCategory[field.field_category] || 0) + 1;
      });
    });
    
    return {
      totalDocuments,
      totalMappings,
      documentsWithFields,
      totalFields,
      fieldsByCategory,
      dataSource: 'newSQL folder'
    };
  }
}

// Export a singleton instance
export const sqlDataService = SQLDataService.getInstance();
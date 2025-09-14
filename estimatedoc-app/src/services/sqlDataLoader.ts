/**
 * SQL Data Loader Service
 * Loads and processes real SQL data from the newSQL directory
 * Implements the mapping approach from MAPPING_APPROACH_DOCUMENTATION.md
 */

import type { Document } from '../types/document.types';

interface SQLDocument {
  id: number;
  filename: string;
  title?: string;
  description?: string;
  category?: string;
  [key: string]: any;
}

interface SQLField {
  id: number;
  name: string;
  type: string;
  category?: string;
  [key: string]: any;
}

interface DocumentField {
  documentId: number;
  fieldId: number;
  count?: number;
  [key: string]: any;
}

interface FieldAnalysis {
  documentId: number;
  fieldId: number;
  fieldType: string;
  complexity?: string;
  effort?: number;
  [key: string]: any;
}

interface ClientRequirement {
  title: string;
  description: string;
  complexity?: string;
  manifestCode?: string;
  sqlDocId?: number;
  [key: string]: any;
}

export class SQLDataLoader {
  private documents: Map<number, SQLDocument> = new Map();
  private fields: Map<number, SQLField> = new Map();
  private documentFields: DocumentField[] = [];
  private fieldAnalyses: FieldAnalysis[] = [];
  private clientRequirements: ClientRequirement[] = [];
  private mappingData: Map<string, any> = new Map();

  /**
   * Load all SQL data from the newSQL directory
   */
  async loadSQLData(): Promise<void> {
    try {
      // Load documents
      const documentsResponse = await fetch('/newSQL/documents.json');
      const documentsData = await documentsResponse.json();
      documentsData.forEach((doc: SQLDocument) => {
        this.documents.set(doc.id, doc);
      });

      // Load fields
      const fieldsResponse = await fetch('/newSQL/fields.json');
      const fieldsData = await fieldsResponse.json();
      fieldsData.forEach((field: SQLField) => {
        this.fields.set(field.id, field);
      });

      // Load document-field relationships
      const docFieldsResponse = await fetch('/newSQL/documentfields.json');
      this.documentFields = await docFieldsResponse.json();

      // Load field analyses
      const analysisResponse = await fetch('/newSQL/field_analysis.json');
      this.fieldAnalyses = await analysisResponse.json();

      console.log(`✅ Loaded SQL data: ${this.documents.size} documents, ${this.fields.size} fields`);
    } catch (error) {
      console.error('❌ Error loading SQL data:', error);
      throw error;
    }
  }

  /**
   * Load client requirements and mapping data
   */
  async loadMappingData(): Promise<void> {
    try {
      // Load client requirements (CSV converted to JSON)
      const reqResponse = await fetch('/ImportantData/ClientRequirements.json');
      this.clientRequirements = await reqResponse.json();

      // Load mapping solution
      const mappingResponse = await fetch('/ClaudeReview/ULTIMATE_Mapping_Solution.json');
      const mappingData = await mappingResponse.json();
      
      // Build mapping index
      mappingData.forEach((item: any) => {
        if (item.clientName) {
          this.mappingData.set(item.clientName, item);
        }
      });

      console.log(`✅ Loaded mapping data: ${this.clientRequirements.length} requirements`);
    } catch (error) {
      console.error('⚠️ Could not load mapping data, will use direct SQL data:', error);
    }
  }

  /**
   * Process and convert SQL data to Document format
   */
  processDocuments(): Document[] {
    const processedDocs: Document[] = [];

    // Process each SQL document
    this.documents.forEach((sqlDoc, docId) => {
      // Get field data for this document
      const docFields = this.documentFields.filter(df => df.documentId === docId);
      const docAnalyses = this.fieldAnalyses.filter(fa => fa.documentId === docId);

      // Count field types based on field analysis
      const fieldTypes = {
        ifStatement: 0,
        precedentScript: 0,
        reflection: 0,
        search: 0,
        unbound: 0,
        builtInScript: 0,
        extended: 0,
        scripted: 0
      };

      // Map field types from analysis
      docAnalyses.forEach(analysis => {
        const fieldType = this.mapFieldType(analysis.fieldType);
        if (fieldType && fieldType in fieldTypes) {
          fieldTypes[fieldType as keyof typeof fieldTypes]++;
        }
      });

      // Try to find mapping from client requirements
      const mapping = this.findMapping(sqlDoc);
      
      // Calculate total fields
      const totalFields = Object.values(fieldTypes).reduce((sum, count) => sum + count, 0);

      // Determine complexity based on field counts and types
      const complexity = this.calculateComplexity(fieldTypes, totalFields);

      // Create Document object
      const doc: Document = {
        id: docId.toString(),
        name: mapping?.clientName || sqlDoc.title || sqlDoc.filename.replace('.dot', ''),
        description: mapping?.description || sqlDoc.description || 'SQL Document',
        template: sqlDoc.filename,
        fields: totalFields,
        fieldTypes,
        complexity: {
          level: complexity,
          factors: {
            fields: totalFields,
            scripts: fieldTypes.precedentScript + fieldTypes.builtInScript + fieldTypes.scripted,
            conditionals: fieldTypes.ifStatement
          }
        },
        effort: {
          base: 0, // Will be calculated by calculator
          optimized: 0,
          savings: 0
        },
        evidence: {
          source: 'SQL' as const,
          confidence: 100,
          lastUpdated: new Date().toISOString()
        },
        reusability: this.estimateReusability(fieldTypes),
        risk: this.assessRisk(complexity, totalFields),
        status: 'pending' as const,
        metadata: {
          sqlDocId: docId,
          sqlFilename: sqlDoc.filename,
          manifestCode: mapping?.manifestCode,
          clientComplexity: mapping?.complexity,
          createdAt: new Date().toISOString()
        },
        totals: {
          allFields: totalFields,
          uniqueFields: Math.floor(totalFields * 0.7),
          reusableFields: Math.floor(totalFields * 0.5),
          reuseRate: '50%'
        }
      };

      processedDocs.push(doc);
    });

    console.log(`✅ Processed ${processedDocs.length} documents from SQL data`);
    return processedDocs;
  }

  /**
   * Map SQL field type to our field type categories
   */
  private mapFieldType(sqlFieldType: string): string | null {
    const typeMap: Record<string, string> = {
      'If': 'ifStatement',
      'If Statement': 'ifStatement',
      'Precedent Script': 'precedentScript',
      'PrecedentScript': 'precedentScript',
      'Reflection': 'reflection',
      'Search': 'search',
      'Unbound': 'unbound',
      'Built In Script': 'builtInScript',
      'BuiltInScript': 'builtInScript',
      'Extended': 'extended',
      'Scripted': 'scripted',
      'Script': 'scripted'
    };

    // Try exact match first
    if (typeMap[sqlFieldType]) {
      return typeMap[sqlFieldType];
    }

    // Try case-insensitive match
    const lowerType = sqlFieldType.toLowerCase();
    for (const [key, value] of Object.entries(typeMap)) {
      if (key.toLowerCase() === lowerType) {
        return value;
      }
    }

    // Check for partial matches
    if (lowerType.includes('if')) return 'ifStatement';
    if (lowerType.includes('precedent')) return 'precedentScript';
    if (lowerType.includes('reflect')) return 'reflection';
    if (lowerType.includes('search')) return 'search';
    if (lowerType.includes('unbound')) return 'unbound';
    if (lowerType.includes('built') && lowerType.includes('script')) return 'builtInScript';
    if (lowerType.includes('extend')) return 'extended';
    if (lowerType.includes('script')) return 'scripted';

    return null;
  }

  /**
   * Find mapping data for a SQL document
   */
  private findMapping(sqlDoc: SQLDocument): any {
    // Try to find by filename (without extension)
    const basename = sqlDoc.filename.replace('.dot', '');
    
    // Direct match
    if (this.mappingData.has(basename)) {
      return this.mappingData.get(basename);
    }

    // Try numeric match (e.g., "2694" for "2694.dot")
    const numericName = basename.match(/\d+/)?.[0];
    if (numericName && this.mappingData.has(numericName)) {
      return this.mappingData.get(numericName);
    }

    // Try to find in client requirements
    const requirement = this.clientRequirements.find(req => 
      req.sqlDocId === sqlDoc.id || 
      req.manifestCode === basename
    );

    if (requirement) {
      return {
        clientName: requirement.title,
        description: requirement.description,
        complexity: requirement.complexity,
        manifestCode: requirement.manifestCode
      };
    }

    return null;
  }

  /**
   * Calculate complexity based on field counts and types
   */
  private calculateComplexity(fieldTypes: any, totalFields: number): 'Simple' | 'Moderate' | 'Complex' {
    const scripts = fieldTypes.precedentScript + fieldTypes.builtInScript + fieldTypes.scripted;
    const conditionals = fieldTypes.ifStatement;

    if (totalFields <= 10 && scripts === 0 && conditionals <= 2) {
      return 'Simple';
    } else if (totalFields <= 20 && scripts <= 5 && conditionals <= 20) {
      return 'Moderate';
    } else {
      return 'Complex';
    }
  }

  /**
   * Estimate reusability based on field types
   */
  private estimateReusability(fieldTypes: any): number {
    const totalFields = Object.values(fieldTypes).reduce((sum: number, count: any) => sum + count, 0);
    if (totalFields === 0) return 100;

    // More scripts = less reusable
    const scripts = fieldTypes.precedentScript + fieldTypes.builtInScript + fieldTypes.scripted;
    const scriptRatio = scripts / totalFields;

    // More conditionals = less reusable
    const conditionalRatio = fieldTypes.ifStatement / totalFields;

    // Calculate reusability (100% - penalties)
    const reusability = Math.max(30, 100 - (scriptRatio * 40) - (conditionalRatio * 20));
    return Math.round(reusability);
  }

  /**
   * Assess risk based on complexity and field count
   */
  private assessRisk(complexity: string, totalFields: number): 'low' | 'medium' | 'high' {
    if (complexity === 'Complex' || totalFields > 30) {
      return 'high';
    } else if (complexity === 'Moderate' || totalFields > 15) {
      return 'medium';
    }
    return 'low';
  }

  /**
   * Main method to load and process all data
   */
  async loadAndProcessDocuments(): Promise<Document[]> {
    console.log('🔄 Loading SQL data from newSQL directory...');
    
    // Load SQL data
    await this.loadSQLData();
    
    // Try to load mapping data (optional)
    await this.loadMappingData();
    
    // Process documents
    const documents = this.processDocuments();
    
    console.log(`✅ Successfully loaded ${documents.length} documents from SQL data`);
    return documents;
  }

  /**
   * Reload data from source files
   */
  async reloadData(): Promise<Document[]> {
    console.log('🔄 Reloading SQL data...');
    
    // Clear existing data
    this.documents.clear();
    this.fields.clear();
    this.documentFields = [];
    this.fieldAnalyses = [];
    this.clientRequirements = [];
    this.mappingData.clear();
    
    // Reload everything
    return this.loadAndProcessDocuments();
  }
}

// Export singleton instance
export const sqlDataLoader = new SQLDataLoader();
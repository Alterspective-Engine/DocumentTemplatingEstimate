#!/usr/bin/env node

/**
 * Process SQL data from newSQL directory and generate JSON files for the app
 * This implements the mapping approach from MAPPING_APPROACH_DOCUMENTATION.md
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths
const ROOT_DIR = path.join(__dirname, '../../');
const SQL_DIR = path.join(ROOT_DIR, 'newSQL');
const IMPORTANT_DATA_DIR = path.join(ROOT_DIR, 'ImportantData');
const CLAUDE_REVIEW_DIR = path.join(ROOT_DIR, 'ClaudeReview');
const APP_PUBLIC_DIR = path.join(__dirname, '../public');

// Ensure public directories exist
if (!fs.existsSync(path.join(APP_PUBLIC_DIR, 'newSQL'))) {
  fs.mkdirSync(path.join(APP_PUBLIC_DIR, 'newSQL'), { recursive: true });
}
if (!fs.existsSync(path.join(APP_PUBLIC_DIR, 'ImportantData'))) {
  fs.mkdirSync(path.join(APP_PUBLIC_DIR, 'ImportantData'), { recursive: true });
}
if (!fs.existsSync(path.join(APP_PUBLIC_DIR, 'ClaudeReview'))) {
  fs.mkdirSync(path.join(APP_PUBLIC_DIR, 'ClaudeReview'), { recursive: true });
}

/**
 * Copy SQL JSON files to public directory
 */
function copySQLFiles() {
  console.log('📋 Copying SQL data files...');
  
  const sqlFiles = [
    'documents.json',
    'fields.json',
    'documentfields.json',
    'field_analysis.json'
  ];
  
  sqlFiles.forEach(file => {
    const source = path.join(SQL_DIR, file);
    const dest = path.join(APP_PUBLIC_DIR, 'newSQL', file);
    
    if (fs.existsSync(source)) {
      fs.copyFileSync(source, dest);
      console.log(`  ✅ Copied ${file}`);
    } else {
      console.log(`  ⚠️ ${file} not found in newSQL directory`);
    }
  });
}

/**
 * Generate TypeScript documents from SQL data
 */
async function generateTypeScriptDocuments() {
  console.log('🔄 Generating TypeScript documents from SQL data...');
  
  // Load SQL data
  const documentsPath = path.join(SQL_DIR, 'documents.json');
  const fieldsPath = path.join(SQL_DIR, 'fields.json');
  const docFieldsPath = path.join(SQL_DIR, 'documentfields.json');
  const analysisPath = path.join(SQL_DIR, 'field_analysis.json');
  
  if (!fs.existsSync(documentsPath)) {
    console.log('  ⚠️ documents.json not found');
    return;
  }
  
  const documents = JSON.parse(fs.readFileSync(documentsPath, 'utf-8'));
  const fields = fs.existsSync(fieldsPath) ? JSON.parse(fs.readFileSync(fieldsPath, 'utf-8')) : [];
  const docFields = fs.existsSync(docFieldsPath) ? JSON.parse(fs.readFileSync(docFieldsPath, 'utf-8')) : [];
  const analyses = fs.existsSync(analysisPath) ? JSON.parse(fs.readFileSync(analysisPath, 'utf-8')) : [];
  
  console.log(`  📊 Loaded: ${documents.length} documents, ${fields.length} fields, ${docFields.length} relationships`);
  
  // Build field type maps from field analysis
  const fieldTypeByDoc = new Map();
  analyses.forEach(analysis => {
    const docId = analysis.documentid || analysis.documentId;
    const fieldCategory = analysis.field_category || analysis.fieldType || analysis.fieldCategory;
    
    if (!fieldTypeByDoc.has(docId)) {
      fieldTypeByDoc.set(docId, {});
    }
    
    const docFieldTypes = fieldTypeByDoc.get(docId);
    const mappedType = mapFieldType(fieldCategory);
    if (mappedType) {
      docFieldTypes[mappedType] = (docFieldTypes[mappedType] || 0) + 1;
    }
  });
  
  // Process documents
  const processedDocs = documents.map(doc => {
    // Get field counts for this document
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
    
    // Count field types from field analysis data
    const docId = doc.DocumentID || doc.id;
    
    // Get field types from our analysis map
    const analyzedFieldTypes = fieldTypeByDoc.get(docId);
    if (analyzedFieldTypes) {
      // Use analyzed field types
      Object.keys(analyzedFieldTypes).forEach(fieldType => {
        if (fieldTypes.hasOwnProperty(fieldType)) {
          fieldTypes[fieldType] = analyzedFieldTypes[fieldType];
        }
      });
    }
    
    const totalFields = Object.values(fieldTypes).reduce((sum, count) => sum + count, 0);
    const complexity = calculateComplexity(fieldTypes, totalFields);
    
    const filename = doc.Filename || doc.filename || doc.FileFullname || '';
    const name = doc.WorkSiteName || doc.title || filename.replace('.dot', '') || `Document_${docId}`;
    
    return {
      id: docId.toString(),
      name: name,
      description: doc.description || doc.WorkSiteName || 'SQL Document',
      template: filename || 'unknown.dot',
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
        base: 0,
        optimized: 0,
        savings: 0
      },
      evidence: {
        source: 'SQL',
        confidence: 100,
        lastUpdated: new Date().toISOString()
      },
      reusability: estimateReusability(fieldTypes, totalFields),
      risk: assessRisk(complexity, totalFields),
      status: 'pending',
      metadata: {
        sqlDocId: docId,
        sqlFilename: filename,
        createdAt: new Date().toISOString()
      },
      // Only include actual data - no fabrication
      totals: {
        allFields: totalFields
        // uniqueFields, reusableFields, and reuseRate must come from actual SQL data
        // Not fabricating these values
      }
    };
  });
  
  // Generate TypeScript file
  const tsContent = `// Auto-generated from SQL data on ${new Date().toISOString()}
// DO NOT EDIT MANUALLY - Run scripts/process-sql-data.js to update

import type { Document } from '../types/document.types';

export const sqlDocuments: Document[] = ${JSON.stringify(processedDocs, null, 2)};

export default sqlDocuments;
`;
  
  const outputPath = path.join(__dirname, '../src/data/sql-documents.ts');
  fs.writeFileSync(outputPath, tsContent);
  console.log(`  ✅ Generated sql-documents.ts with ${processedDocs.length} documents`);
}

/**
 * Map SQL field type to our categories
 */
function mapFieldType(sqlFieldType) {
  if (!sqlFieldType) return null;
  
  const typeMap = {
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
  
  // Try exact match
  if (typeMap[sqlFieldType]) return typeMap[sqlFieldType];
  
  // Try case-insensitive
  const lower = sqlFieldType.toLowerCase();
  for (const [key, value] of Object.entries(typeMap)) {
    if (key.toLowerCase() === lower) return value;
  }
  
  // Partial matches
  if (lower.includes('if')) return 'ifStatement';
  if (lower.includes('precedent')) return 'precedentScript';
  if (lower.includes('reflect')) return 'reflection';
  if (lower.includes('search')) return 'search';
  if (lower.includes('unbound')) return 'unbound';
  if (lower.includes('built') && lower.includes('script')) return 'builtInScript';
  if (lower.includes('extend')) return 'extended';
  if (lower.includes('script')) return 'scripted';
  
  return null;
}

/**
 * Calculate complexity
 */
function calculateComplexity(fieldTypes, totalFields) {
  const scripts = fieldTypes.precedentScript + fieldTypes.builtInScript + fieldTypes.scripted;
  const conditionals = fieldTypes.ifStatement;
  
  if (totalFields <= 10 && scripts === 0 && conditionals <= 2) {
    return 'Simple';
  } else if (totalFields <= 20 && scripts <= 5 && conditionals <= 20) {
    return 'Moderate';
  }
  return 'Complex';
}

/**
 * Estimate reusability
 */
function estimateReusability(fieldTypes, totalFields) {
  if (totalFields === 0) return 100;
  
  const scripts = fieldTypes.precedentScript + fieldTypes.builtInScript + fieldTypes.scripted;
  const scriptRatio = scripts / totalFields;
  const conditionalRatio = fieldTypes.ifStatement / totalFields;
  
  const reusability = Math.max(30, 100 - (scriptRatio * 40) - (conditionalRatio * 20));
  return Math.round(reusability);
}

/**
 * Assess risk
 */
function assessRisk(complexity, totalFields) {
  if (complexity === 'Complex' || totalFields > 30) return 'high';
  if (complexity === 'Moderate' || totalFields > 15) return 'medium';
  return 'low';
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 Processing SQL data for EstimateDoc application\n');
  
  // Copy SQL files
  copySQLFiles();
  
  // Generate TypeScript documents
  await generateTypeScriptDocuments();
  
  console.log('\n✅ SQL data processing complete!');
  console.log('📝 Next steps:');
  console.log('  1. Update src/store/documentStore.ts to use sqlDocuments');
  console.log('  2. Run npm run build to verify');
  console.log('  3. Test the application with real SQL data');
}

// Run script
main().catch(error => {
  console.error('❌ Error processing SQL data:', error);
  process.exit(1);
});

export { main };
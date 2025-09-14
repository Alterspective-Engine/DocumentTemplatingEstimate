#!/usr/bin/env node

/**
 * Script to extract data from SQLite database to JSON file
 * This allows us to use real database data in the frontend application
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Connect to the database
const dbPath = path.join(__dirname, '../src/database/estimatedoc_complete.db');
const db = new Database(dbPath, {
  readonly: true,
  fileMustExist: true
});

console.log('📊 Extracting data from database...');

try {
  // Get all documents from database
  const stmt = db.prepare(`
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
  const documents = rows.map((row) => ({
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
    reusability: calculateReusability(row),
    
    // Risk assessment
    risk: assessRisk(row),
    
    // Status tracking
    status: 'pending',
    
    // Metadata
    metadata: {
      sqlDocId: row.sql_doc_id,
      sqlFilename: row.sql_filename,
      manifestCode: row.manifest_code,
      clientComplexity: row.client_complexity,
      createdAt: row.created_at
    }
  }));
  
  // Write to JSON file
  const outputPath = path.join(__dirname, '../src/data/database-documents.json');
  fs.writeFileSync(outputPath, JSON.stringify(documents, null, 2));
  
  console.log(`✅ Extracted ${documents.length} documents to ${outputPath}`);
  
  // Also create a TypeScript file that exports the data
  const tsContent = `// Auto-generated from database on ${new Date().toISOString()}
// DO NOT EDIT MANUALLY - Run scripts/extract-db-data.js to update

import type { Document } from '../types/document.types';

export const databaseDocuments: Document[] = ${JSON.stringify(documents, null, 2)};

export default databaseDocuments;
`;
  
  const tsOutputPath = path.join(__dirname, '../src/data/database-documents.ts');
  fs.writeFileSync(tsOutputPath, tsContent);
  
  console.log(`✅ Created TypeScript file at ${tsOutputPath}`);
  
} catch (error) {
  console.error('❌ Error extracting data:', error);
  process.exit(1);
} finally {
  db.close();
}

/**
 * Calculate reusability score based on document characteristics
 */
function calculateReusability(row) {
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
function assessRisk(row) {
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
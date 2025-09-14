#!/usr/bin/env node

/**
 * Import all SQL JSON data into SQLite database
 * This creates a single source of truth for all document data
 * Preserves user settings (calculator configurations) during reimport
 */

import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths
const ROOT_DIR = path.join(__dirname, '../../');
const SQL_DIR = path.join(ROOT_DIR, 'newSQL');
const IMPORTANT_DATA_DIR = path.join(ROOT_DIR, 'ImportantData');
const DB_PATH = path.join(__dirname, '../src/database/estimatedoc.db');

// Connect to database
let db;

/**
 * Initialize database connection
 */
function initDatabase() {
  console.log('📊 Connecting to SQLite database...');
  
  // Create database directory if it doesn't exist
  const dbDir = path.dirname(DB_PATH);
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }
  
  db = new Database(DB_PATH, {
    verbose: console.log
  });
  
  // Enable foreign keys and optimize
  db.pragma('foreign_keys = ON');
  db.pragma('journal_mode = WAL');
  db.pragma('synchronous = NORMAL');
  
  console.log('✅ Database connected');
}

/**
 * Create database schema
 */
function createSchema() {
  console.log('🔨 Creating database schema...');
  
  // Drop existing tables (except settings)
  db.exec(`
    DROP TABLE IF EXISTS field_analysis;
    DROP TABLE IF EXISTS document_fields;
    DROP TABLE IF EXISTS fields;
    DROP TABLE IF EXISTS documents;
  `);
  
  // Create settings table if it doesn't exist
  db.exec(`
    CREATE TABLE IF NOT EXISTS settings (
      id INTEGER PRIMARY KEY,
      key TEXT UNIQUE NOT NULL,
      value TEXT NOT NULL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  // Create documents table
  db.exec(`
    CREATE TABLE documents (
      id INTEGER PRIMARY KEY,
      filename TEXT,
      worksitename TEXT,
      description TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  // Create fields table
  db.exec(`
    CREATE TABLE fields (
      id INTEGER PRIMARY KEY,
      displayname TEXT,
      worksitename TEXT,
      guid TEXT UNIQUE,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  
  // Create document_fields relationship table
  db.exec(`
    CREATE TABLE document_fields (
      id INTEGER PRIMARY KEY,
      document_id INTEGER NOT NULL,
      field_id INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
      FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
      UNIQUE(document_id, field_id)
    );
  `);
  
  // Create field_analysis table
  db.exec(`
    CREATE TABLE field_analysis (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id INTEGER NOT NULL,
      filename TEXT,
      fieldcode TEXT,
      fieldresult TEXT,
      field_category TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
  `);
  
  // Create indexes for performance
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
    CREATE INDEX IF NOT EXISTS idx_fields_guid ON fields(guid);
    CREATE INDEX IF NOT EXISTS idx_document_fields_doc ON document_fields(document_id);
    CREATE INDEX IF NOT EXISTS idx_document_fields_field ON document_fields(field_id);
    CREATE INDEX IF NOT EXISTS idx_field_analysis_doc ON field_analysis(document_id);
    CREATE INDEX IF NOT EXISTS idx_field_analysis_category ON field_analysis(field_category);
  `);
  
  console.log('✅ Schema created');
}

/**
 * Import documents from JSON
 */
function importDocuments() {
  console.log('📥 Importing documents...');
  
  const documentsPath = path.join(SQL_DIR, 'documents.json');
  if (!fs.existsSync(documentsPath)) {
    console.error('❌ documents.json not found');
    return 0;
  }
  
  const documents = JSON.parse(fs.readFileSync(documentsPath, 'utf-8'));
  
  const stmt = db.prepare(`
    INSERT INTO documents (id, filename, worksitename, description)
    VALUES (?, ?, ?, ?)
  `);
  
  const insertMany = db.transaction((docs) => {
    for (const doc of docs) {
      stmt.run(
        doc.DocumentID || doc.id,
        doc.Filename || doc.filename || doc.FileFullname || '',
        doc.WorkSiteName || doc.worksitename || '',
        doc.description || doc.WorkSiteName || 'SQL Document'
      );
    }
  });
  
  insertMany(documents);
  console.log(`✅ Imported ${documents.length} documents`);
  return documents.length;
}

/**
 * Import fields from JSON
 */
function importFields() {
  console.log('📥 Importing fields...');
  
  const fieldsPath = path.join(SQL_DIR, 'fields.json');
  if (!fs.existsSync(fieldsPath)) {
    console.error('❌ fields.json not found');
    return 0;
  }
  
  const fields = JSON.parse(fs.readFileSync(fieldsPath, 'utf-8'));
  
  const stmt = db.prepare(`
    INSERT INTO fields (id, displayname, worksitename, guid)
    VALUES (?, ?, ?, ?)
  `);
  
  const insertMany = db.transaction((flds) => {
    for (const field of flds) {
      stmt.run(
        field.FieldID || field.id,
        field.DisplayName || field.displayname || '',
        field.WorkSiteName || field.worksitename || '',
        field.GUID || field.guid || ''
      );
    }
  });
  
  insertMany(fields);
  console.log(`✅ Imported ${fields.length} fields`);
  return fields.length;
}

/**
 * Import document-field relationships
 */
function importDocumentFields() {
  console.log('📥 Importing document-field relationships...');
  
  const docFieldsPath = path.join(SQL_DIR, 'documentfields.json');
  if (!fs.existsSync(docFieldsPath)) {
    console.error('❌ documentfields.json not found');
    return 0;
  }
  
  const docFields = JSON.parse(fs.readFileSync(docFieldsPath, 'utf-8'));
  
  const stmt = db.prepare(`
    INSERT OR IGNORE INTO document_fields (document_id, field_id)
    VALUES (?, ?)
  `);
  
  const insertMany = db.transaction((relations) => {
    for (const rel of relations) {
      const docId = rel.DocumentID || rel.documentid;
      const fieldId = rel.FieldID || rel.fieldid;
      
      if (docId && fieldId) {
        stmt.run(docId, fieldId);
      }
    }
  });
  
  insertMany(docFields);
  console.log(`✅ Imported ${docFields.length} document-field relationships`);
  return docFields.length;
}

/**
 * Import field analysis data
 */
function importFieldAnalysis() {
  console.log('📥 Importing field analysis...');
  
  const analysisPath = path.join(SQL_DIR, 'field_analysis.json');
  if (!fs.existsSync(analysisPath)) {
    console.error('❌ field_analysis.json not found');
    return 0;
  }
  
  const analyses = JSON.parse(fs.readFileSync(analysisPath, 'utf-8'));
  
  const stmt = db.prepare(`
    INSERT INTO field_analysis (document_id, filename, fieldcode, fieldresult, field_category)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  const insertMany = db.transaction((items) => {
    for (const item of items) {
      stmt.run(
        item.documentid || item.documentId,
        item.filename || '',
        item.fieldcode || '',
        item.fieldresult || '',
        item.field_category || item.fieldType || item.fieldCategory || ''
      );
    }
  });
  
  insertMany(analyses);
  console.log(`✅ Imported ${analyses.length} field analysis records`);
  return analyses.length;
}

/**
 * Import additional data from ImportantData folder
 */
function importImportantData() {
  console.log('📥 Checking for ImportantData...');
  
  if (!fs.existsSync(IMPORTANT_DATA_DIR)) {
    console.log('⚠️ ImportantData directory not found, skipping');
    return;
  }
  
  // Look for any JSON files in ImportantData
  const files = fs.readdirSync(IMPORTANT_DATA_DIR).filter(f => f.endsWith('.json'));
  
  for (const file of files) {
    console.log(`  Processing ${file}...`);
    const filePath = path.join(IMPORTANT_DATA_DIR, file);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    
    // Store in settings table as JSON for now
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO settings (key, value)
      VALUES (?, ?)
    `);
    
    stmt.run(`important_data_${file}`, JSON.stringify(data));
  }
  
  if (files.length > 0) {
    console.log(`✅ Imported ${files.length} ImportantData files`);
  }
}

/**
 * Create materialized view for fast document queries
 */
function createMaterializedView() {
  console.log('🔨 Creating materialized view for documents...');
  
  // Drop existing view
  db.exec(`DROP VIEW IF EXISTS documents_complete`);
  
  // Create view with all calculated fields
  db.exec(`
    CREATE VIEW documents_complete AS
    SELECT 
      d.id,
      d.filename,
      d.worksitename as name,
      d.description,
      
      -- Field counts by type
      COUNT(CASE WHEN fa.field_category IN ('If', 'If Statement') THEN 1 END) as if_count,
      COUNT(CASE WHEN fa.field_category IN ('Precedent Script', 'PrecedentScript') THEN 1 END) as precedent_script_count,
      COUNT(CASE WHEN fa.field_category = 'Reflection' THEN 1 END) as reflection_count,
      COUNT(CASE WHEN fa.field_category = 'Search' THEN 1 END) as search_count,
      COUNT(CASE WHEN fa.field_category = 'Unbound' THEN 1 END) as unbound_count,
      COUNT(CASE WHEN fa.field_category IN ('Built In Script', 'BuiltInScript') THEN 1 END) as built_in_script_count,
      COUNT(CASE WHEN fa.field_category = 'Extended' THEN 1 END) as extended_count,
      COUNT(CASE WHEN fa.field_category IN ('Scripted', 'Script') THEN 1 END) as scripted_count,
      
      -- Total fields
      COUNT(fa.id) as total_fields,
      
      -- Complexity calculation
      CASE
        WHEN COUNT(fa.id) <= 10 
          AND COUNT(CASE WHEN fa.field_category LIKE '%Script%' THEN 1 END) = 0 
          AND COUNT(CASE WHEN fa.field_category LIKE '%If%' THEN 1 END) <= 2
        THEN 'Simple'
        WHEN COUNT(fa.id) <= 20 
          AND COUNT(CASE WHEN fa.field_category LIKE '%Script%' THEN 1 END) <= 5 
          AND COUNT(CASE WHEN fa.field_category LIKE '%If%' THEN 1 END) <= 20
        THEN 'Moderate'
        ELSE 'Complex'
      END as complexity_level,
      
      -- Reusability score (calculated from field types)
      CASE
        WHEN COUNT(fa.id) = 0 THEN 100
        ELSE CAST(
          MAX(30, 
            100 - (
              (CAST(COUNT(CASE WHEN fa.field_category LIKE '%Script%' THEN 1 END) AS FLOAT) / COUNT(fa.id) * 40) +
              (CAST(COUNT(CASE WHEN fa.field_category LIKE '%If%' THEN 1 END) AS FLOAT) / COUNT(fa.id) * 20)
            )
          ) AS INTEGER
        )
      END as reusability,
      
      'SQL' as data_source,
      d.created_at,
      d.updated_at
      
    FROM documents d
    LEFT JOIN field_analysis fa ON d.id = fa.document_id
    GROUP BY d.id, d.filename, d.worksitename, d.description, d.created_at, d.updated_at
  `);
  
  console.log('✅ Materialized view created');
}

/**
 * Update import timestamp
 */
function updateImportTimestamp() {
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO settings (key, value)
    VALUES ('last_import', ?)
  `);
  
  stmt.run(new Date().toISOString());
}

/**
 * Get import statistics
 */
function getImportStats() {
  const stats = {
    documents: db.prepare('SELECT COUNT(*) as count FROM documents').get().count,
    fields: db.prepare('SELECT COUNT(*) as count FROM fields').get().count,
    relationships: db.prepare('SELECT COUNT(*) as count FROM document_fields').get().count,
    analyses: db.prepare('SELECT COUNT(*) as count FROM field_analysis').get().count,
    documentsWithFields: db.prepare(`
      SELECT COUNT(DISTINCT document_id) as count 
      FROM field_analysis
    `).get().count
  };
  
  return stats;
}

/**
 * Main import function
 */
export async function importAllData(preserveSettings = true) {
  try {
    console.log('🚀 Starting SQLite data import...\n');
    
    // Initialize database
    initDatabase();
    
    // Save settings if preserving
    let savedSettings = null;
    if (preserveSettings) {
      console.log('💾 Preserving user settings...');
      try {
        savedSettings = db.prepare('SELECT * FROM settings WHERE key LIKE "calculator_%"').all();
      } catch (e) {
        console.log('  No existing settings to preserve');
      }
    }
    
    // Create schema (drops existing data tables)
    createSchema();
    
    // Restore settings if preserved
    if (savedSettings && savedSettings.length > 0) {
      console.log('♻️ Restoring user settings...');
      const stmt = db.prepare('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)');
      for (const setting of savedSettings) {
        stmt.run(setting.key, setting.value);
      }
    }
    
    // Import all data
    importDocuments();
    importFields();
    importDocumentFields();
    importFieldAnalysis();
    importImportantData();
    
    // Create materialized view
    createMaterializedView();
    
    // Update timestamp
    updateImportTimestamp();
    
    // Get statistics
    const stats = getImportStats();
    
    console.log('\n📊 Import Summary:');
    console.log(`  Documents: ${stats.documents}`);
    console.log(`  Fields: ${stats.fields}`);
    console.log(`  Relationships: ${stats.relationships}`);
    console.log(`  Field Analyses: ${stats.analyses}`);
    console.log(`  Documents with field data: ${stats.documentsWithFields}`);
    
    console.log('\n✅ SQLite import completed successfully!');
    
    // Close database
    db.close();
    
    return { success: true, stats };
    
  } catch (error) {
    console.error('❌ Import failed:', error);
    if (db) db.close();
    return { success: false, error: error.message };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  importAllData(true);
}
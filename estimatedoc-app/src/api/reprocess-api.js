/**
 * API endpoint for reprocessing data
 * Clears database and reimports from newSQL while preserving settings
 */

import express from 'express';
import { importAllData } from '../../scripts/import-to-sqlite.js';
import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const router = express.Router();

/**
 * GET /api/reprocess/status
 * Get current data status
 */
router.get('/status', (req, res) => {
  try {
    const dbPath = path.join(__dirname, '../database/estimatedoc.db');
    const db = new Database(dbPath, { readonly: true });
    
    const stats = {
      documents: db.prepare('SELECT COUNT(*) as count FROM documents').get()?.count || 0,
      fields: db.prepare('SELECT COUNT(*) as count FROM fields').get()?.count || 0,
      analyses: db.prepare('SELECT COUNT(*) as count FROM field_analysis').get()?.count || 0,
      lastImport: db.prepare('SELECT value FROM settings WHERE key = "last_import"').get()?.value || null
    };
    
    db.close();
    
    res.json({
      success: true,
      stats
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/reprocess/import
 * Trigger full data reimport
 */
router.post('/import', async (req, res) => {
  try {
    console.log('🔄 Reprocessing data request received...');
    
    // Get preserve settings option from request
    const preserveSettings = req.body?.preserveSettings !== false;
    
    // Run import
    const result = await importAllData(preserveSettings);
    
    if (result.success) {
      res.json({
        success: true,
        message: 'Data reprocessed successfully',
        stats: result.stats
      });
    } else {
      res.status(500).json({
        success: false,
        error: result.error
      });
    }
  } catch (error) {
    console.error('❌ Reprocess failed:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/reprocess/calculator-settings
 * Get current calculator settings from database
 */
router.get('/calculator-settings', (req, res) => {
  try {
    const dbPath = path.join(__dirname, '../database/estimatedoc.db');
    const db = new Database(dbPath, { readonly: true });
    
    const settings = db.prepare(`
      SELECT key, value 
      FROM settings 
      WHERE key LIKE 'calculator_%'
    `).all();
    
    db.close();
    
    const settingsObj = {};
    for (const setting of settings) {
      settingsObj[setting.key] = JSON.parse(setting.value);
    }
    
    res.json({
      success: true,
      settings: settingsObj
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * POST /api/reprocess/calculator-settings
 * Save calculator settings to database
 */
router.post('/calculator-settings', (req, res) => {
  try {
    const dbPath = path.join(__dirname, '../database/estimatedoc.db');
    const db = new Database(dbPath);
    
    const { settings } = req.body;
    
    if (!settings) {
      return res.status(400).json({
        success: false,
        error: 'No settings provided'
      });
    }
    
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO settings (key, value, updated_at)
      VALUES (?, ?, CURRENT_TIMESTAMP)
    `);
    
    const saveSettings = db.transaction(() => {
      for (const [key, value] of Object.entries(settings)) {
        stmt.run(`calculator_${key}`, JSON.stringify(value));
      }
    });
    
    saveSettings();
    db.close();
    
    res.json({
      success: true,
      message: 'Settings saved successfully'
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;
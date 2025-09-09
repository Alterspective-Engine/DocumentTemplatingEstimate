import express from 'express';
import cors from 'cors';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { createTemplateDetailsRouter } from './template-details';

dotenv.config();

export function createPool() {
  return new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'estimatedoc',
    user: process.env.DB_USER || 'estimatedoc_user',
    password: process.env.DB_PASSWORD || 'estimatedoc_user',
  });
}

export function createApp(pool: Pool) {
  const app = express();

  app.use(cors());
  app.use(express.json());

  // Mount the template details router
  app.use('/api', createTemplateDetailsRouter(pool));

  // Health check
  app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Stats and templates routes (from former index.ts)
  app.get('/api/stats/overview', async (req, res) => {
    try {
      const result = await pool.query(`
      WITH excel_documents AS (
        SELECT DISTINCT tm.document_id
        FROM template_matches tm
        WHERE tm.document_id IS NOT NULL
      )
      SELECT 
        (SELECT COUNT(DISTINCT document_id) FROM excel_documents) as total_documents,
        (SELECT COUNT(DISTINCT f.field_id) 
         FROM fields f 
         JOIN document_fields df ON f.field_id = df.field_id
         WHERE df.document_id IN (SELECT document_id FROM excel_documents)) as total_fields,
        (SELECT COUNT(*) FROM excel_templates) as total_templates,
        (SELECT COUNT(*) FROM template_matches WHERE document_id IS NOT NULL) as matched_templates,
        (SELECT COUNT(DISTINCT stated_complexity) FROM excel_templates WHERE stated_complexity IS NOT NULL) as complexity_levels,
        (SELECT COUNT(DISTINCT manifest_code) FROM template_matches WHERE manifest_code IS NOT NULL) as unique_precedents
    `);
      const stats = result.rows[0] as any;
      stats.match_rate = ((stats.matched_templates / stats.total_templates) * 100).toFixed(1);
      res.json(stats);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching overview stats:', error);
      res.status(500).json({ error: 'Failed to fetch statistics' });
    }
  });

  app.get('/api/stats/complexity-distribution', async (req, res) => {
    try {
      const result = await pool.query(`
      SELECT 
        et.stated_complexity,
        COUNT(*) as count,
        COUNT(CASE WHEN tm.document_id IS NOT NULL THEN 1 END) as matched_count,
        COUNT(CASE WHEN tm.document_id IS NULL THEN 1 END) as unmatched_count
      FROM excel_templates et
      LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
      WHERE et.stated_complexity IS NOT NULL
      GROUP BY et.stated_complexity
      ORDER BY 
        CASE et.stated_complexity
          WHEN 'Simple' THEN 1
          WHEN 'Moderate' THEN 2
          WHEN 'Medium' THEN 3
          WHEN 'Complex' THEN 4
          ELSE 5
        END
    `);
      res.json(result.rows);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching complexity distribution:', error);
      res.status(500).json({ error: 'Failed to fetch complexity distribution' });
    }
  });

  app.get('/api/stats/matching', async (req, res) => {
    try {
      const result = await pool.query(`
      SELECT 
        COALESCE(match_method, 'unmatched') as match_method,
        COALESCE(match_confidence, 'None') as match_confidence,
        COUNT(*) as count
      FROM excel_templates et
      LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
      GROUP BY match_method, match_confidence
      ORDER BY 
        CASE match_confidence
          WHEN 'High' THEN 1
          WHEN 'Medium' THEN 2
          WHEN 'Low' THEN 3
          ELSE 4
        END,
        match_method
    `);
      res.json(result.rows);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching matching stats:', error);
      res.status(500).json({ error: 'Failed to fetch matching statistics' });
    }
  });

  app.get('/api/stats/field-reusability', async (req, res) => {
    try {
      const result = await pool.query(`
      WITH excel_documents AS (
        SELECT DISTINCT tm.document_id
        FROM template_matches tm
        WHERE tm.document_id IS NOT NULL
      ),
      field_stats AS (
        SELECT 
          f.field_id,
          f.field_code,
          COUNT(DISTINCT df.document_id) as doc_count,
          SUM(df.count) as total_usage
        FROM fields f
        JOIN document_fields df ON f.field_id = df.field_id
        WHERE df.document_id IN (SELECT document_id FROM excel_documents)
        GROUP BY f.field_id, f.field_code
      )
      SELECT 
        CASE 
          WHEN doc_count = 1 THEN 'Unique'
          WHEN doc_count BETWEEN 2 AND 5 THEN 'Low Reuse (2-5)'
          WHEN doc_count BETWEEN 6 AND 20 THEN 'Medium Reuse (6-20)'
          WHEN doc_count > 20 THEN 'High Reuse (>20)'
        END as reusability_category,
        COUNT(*) as field_count,
        SUM(total_usage) as total_usage
      FROM field_stats
      GROUP BY reusability_category
      ORDER BY 
        CASE reusability_category
          WHEN 'Unique' THEN 1
          WHEN 'Low Reuse (2-5)' THEN 2
          WHEN 'Medium Reuse (6-20)' THEN 3
          WHEN 'High Reuse (>20)' THEN 4
        END
    `);
      res.json(result.rows);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching field reusability:', error);
      res.status(500).json({ error: 'Failed to fetch field reusability' });
    }
  });

  app.get('/api/templates', async (req, res) => {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const offset = parseInt(req.query.offset as string) || 0;
      const result = await pool.query(`
      SELECT 
        et.row_id,
        et.template_code,
        et.description,
        et.stated_complexity,
        tm.match_method,
        tm.match_confidence,
        tm.document_id,
        d.filename as document_filename,
        dc.total_fields,
        dc.if_statements,
        dc.nested_if_statements,
        dc.complexity_rating,
        CASE 
          WHEN tm.document_id IS NOT NULL THEN 'Matched'
          ELSE 'Unmatched'
        END as match_status
      FROM excel_templates et
      LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
      LEFT JOIN documents d ON tm.document_id = d.document_id
      LEFT JOIN document_complexity dc ON d.document_id = dc.document_id
      ORDER BY et.row_id
      LIMIT $1 OFFSET $2
      `, [limit, offset]);
      const countResult = await pool.query('SELECT COUNT(*) FROM excel_templates');
      res.json({
        templates: result.rows,
        total: parseInt(countResult.rows[0].count),
        limit,
        offset
      });
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching templates:', error);
      res.status(500).json({ error: 'Failed to fetch templates' });
    }
  });

  app.get('/api/stats/complexity-trends', async (req, res) => {
    try {
      const result = await pool.query(`
      WITH matched_templates AS (
        SELECT 
          et.stated_complexity,
          dc.total_fields,
          dc.if_statements,
          dc.nested_if_statements,
          dc.total_complexity_score
        FROM excel_templates et
        JOIN template_matches tm ON et.row_id = tm.excel_row_id
        JOIN document_complexity dc ON tm.document_id = dc.document_id
        WHERE et.stated_complexity IS NOT NULL
          AND tm.document_id IS NOT NULL
      )
      SELECT 
        stated_complexity,
        AVG(total_fields) as avg_fields,
        AVG(if_statements) as avg_if_statements,
        AVG(nested_if_statements) as avg_nested_if,
        AVG(total_complexity_score) as avg_complexity_score,
        COUNT(*) as sample_size,
        MIN(total_fields) as min_fields,
        MAX(total_fields) as max_fields,
        STDDEV(total_fields) as stddev_fields
      FROM matched_templates
      GROUP BY stated_complexity
      ORDER BY 
        CASE stated_complexity
          WHEN 'Simple' THEN 1
          WHEN 'Moderate' THEN 2
          WHEN 'Medium' THEN 3
          WHEN 'Complex' THEN 4
          ELSE 5
        END
    `);
      res.json(result.rows);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching complexity trends:', error);
      res.status(500).json({ error: 'Failed to fetch complexity trends' });
    }
  });

  app.get('/api/stats/unmatched', async (req, res) => {
    try {
      const result = await pool.query(`
      SELECT 
        et.stated_complexity,
        COUNT(*) as count,
        array_agg(DISTINCT et.template_code) FILTER (WHERE et.template_code IS NOT NULL) as sample_codes
      FROM excel_templates et
      LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
      WHERE tm.document_id IS NULL
      GROUP BY et.stated_complexity
      ORDER BY count DESC
    `);
      res.json(result.rows);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching unmatched templates:', error);
      res.status(500).json({ error: 'Failed to fetch unmatched templates' });
    }
  });

  app.get('/api/stats/excel-summary', async (req, res) => {
    try {
      const result = await pool.query(`
      WITH summary AS (
        SELECT 
          COUNT(*) as total_excel_rows,
          COUNT(CASE WHEN tm.document_id IS NOT NULL THEN 1 END) as matched_rows,
          COUNT(CASE WHEN tm.document_id IS NULL THEN 1 END) as unmatched_rows,
          COUNT(DISTINCT et.stated_complexity) as complexity_levels,
          COUNT(DISTINCT tm.match_method) FILTER (WHERE tm.match_method IS NOT NULL) as matching_methods_used
        FROM excel_templates et
        LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
      )
      SELECT 
        *,
        ROUND(100.0 * matched_rows / total_excel_rows, 1) as match_percentage
      FROM summary
    `);
      res.json(result.rows[0]);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error fetching Excel summary:', error);
      res.status(500).json({ error: 'Failed to fetch Excel summary' });
    }
  });

  return app;
}

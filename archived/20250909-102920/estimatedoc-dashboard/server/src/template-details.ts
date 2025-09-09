import { Router } from 'express';
import { Pool } from 'pg';

export function createTemplateDetailsRouter(pool: Pool): Router {
  const router = Router();

  // Get detailed information for a specific template with full evidence
  router.get('/templates/:rowId/details', async (req, res) => {
    const { rowId } = req.params;
    
    try {
      // Main template information with all calculations
      const templateQuery = `
        WITH template_fields AS (
          SELECT 
            f.field_id,
            f.field_code,
            f.field_result,
            df.count as usage_count,
            -- Evidence: How many other documents use this field
            (SELECT COUNT(DISTINCT document_id) 
             FROM document_fields df2 
             WHERE df2.field_id = f.field_id) as used_in_documents,
            -- Evidence: Which other templates share this field
            (SELECT STRING_AGG(DISTINCT et2.template_code, ', ' ORDER BY et2.template_code)
             FROM document_fields df2
             JOIN template_matches tm2 ON df2.document_id = tm2.document_id
             JOIN excel_templates et2 ON tm2.excel_row_id = et2.row_id
             WHERE df2.field_id = f.field_id 
               AND et2.row_id != $1) as shared_with_templates
          FROM template_matches tm
          JOIN document_fields df ON tm.document_id = df.document_id
          JOIN fields f ON df.field_id = f.field_id
          WHERE tm.excel_row_id = $1
        )
        SELECT 
          et.row_id,
          et.template_code,
          et.description,
          et.stated_complexity,
          -- Matching evidence
          tm.match_method,
          tm.match_confidence,
          tm.manifest_code,
          tm.manifest_name,
          -- Document evidence
          d.document_id,
          d.filename as document_filename,
          d.basename as document_basename,
          -- Field statistics with evidence
          (SELECT COUNT(DISTINCT field_id) FROM template_fields) as total_fields,
          (SELECT COUNT(DISTINCT field_id) FROM template_fields WHERE used_in_documents = 1) as unique_fields,
          (SELECT COUNT(DISTINCT field_id) FROM template_fields WHERE used_in_documents > 1) as shared_fields,
          -- Complexity evidence from document_complexity table
          dc.total_fields as dc_total_fields,
          dc.docvariable_fields,
          dc.mergefield_fields,
          dc.if_statements,
          dc.nested_if_statements,
          dc.user_input_fields,
          dc.calculated_fields,
          dc.total_complexity_score,
          dc.complexity_rating,
          -- Calculated metrics
          CASE 
            WHEN (SELECT COUNT(*) FROM template_fields) > 0 
            THEN ROUND(100.0 * (SELECT COUNT(*) FROM template_fields WHERE used_in_documents > 1) / 
                      (SELECT COUNT(*) FROM template_fields), 1)
            ELSE 0
          END as reusability_percentage,
          -- Validation evidence
          CASE 
            WHEN et.stated_complexity = 'Simple' AND COALESCE(dc.total_complexity_score, 0) <= 10 THEN 'Matches'
            WHEN et.stated_complexity = 'Moderate' AND COALESCE(dc.total_complexity_score, 0) BETWEEN 11 AND 25 THEN 'Matches'
            WHEN et.stated_complexity = 'Complex' AND COALESCE(dc.total_complexity_score, 0) > 25 THEN 'Matches'
            ELSE 'Mismatch'
          END as complexity_validation
        FROM excel_templates et
        LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
        LEFT JOIN documents d ON tm.document_id = d.document_id
        LEFT JOIN document_complexity dc ON d.document_id = dc.document_id
        WHERE et.row_id = $1
      `;
      
      const result = await pool.query(templateQuery, [rowId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Template not found' });
      }
      
      const template = result.rows[0];
      
      // Get detailed field list with evidence
      const fieldsQuery = `
        SELECT 
          f.field_id,
          f.field_code,
          f.field_result,
          df.count as usage_in_this_doc,
          -- Field type classification
          CASE 
            WHEN f.field_code LIKE '%DOCVARIABLE%' THEN 'DOCVARIABLE'
            WHEN f.field_code LIKE '%MERGEFIELD%' THEN 'MERGEFIELD'
            WHEN f.field_code LIKE '%IF %' THEN 'CONDITIONAL'
            WHEN f.field_code LIKE '%ASK%' OR f.field_code LIKE '%FILLIN%' THEN 'USER_INPUT'
            WHEN f.field_code LIKE '%=%' OR f.field_code LIKE '%FORMULA%' THEN 'CALCULATED'
            ELSE 'OTHER'
          END as field_type,
          -- Reusability evidence
          (SELECT COUNT(DISTINCT document_id) 
           FROM document_fields df2 
           WHERE df2.field_id = f.field_id) as total_document_usage,
          (SELECT COUNT(DISTINCT tm2.excel_row_id)
           FROM document_fields df2
           JOIN template_matches tm2 ON df2.document_id = tm2.document_id
           WHERE df2.field_id = f.field_id) as total_template_usage,
          -- List of templates sharing this field
          (SELECT STRING_AGG(DISTINCT et2.template_code, ', ' ORDER BY et2.template_code)
           FROM document_fields df2
           JOIN template_matches tm2 ON df2.document_id = tm2.document_id
           JOIN excel_templates et2 ON tm2.excel_row_id = et2.row_id
           WHERE df2.field_id = f.field_id 
             AND et2.row_id != $1
           LIMIT 10) as shared_with_templates
        FROM template_matches tm
        JOIN document_fields df ON tm.document_id = df.document_id
        JOIN fields f ON df.field_id = f.field_id
        WHERE tm.excel_row_id = $1
        ORDER BY 
          CASE 
            WHEN f.field_code LIKE '%IF %' THEN 1
            WHEN f.field_code LIKE '%DOCVARIABLE%' THEN 2
            WHEN f.field_code LIKE '%MERGEFIELD%' THEN 3
            ELSE 4
          END,
          f.field_code
        LIMIT 100
      `;
      
      const fieldsResult = await pool.query(fieldsQuery, [rowId]);
      
      // Get sharing relationships
      const sharingQuery = `
        WITH this_template_fields AS (
          SELECT DISTINCT df.field_id
          FROM template_matches tm
          JOIN document_fields df ON tm.document_id = df.document_id
          WHERE tm.excel_row_id = $1
        )
        SELECT 
          et2.row_id as related_template_id,
          et2.template_code as related_template_code,
          et2.stated_complexity as related_complexity,
          COUNT(DISTINCT df2.field_id) as shared_field_count,
          ROUND(100.0 * COUNT(DISTINCT df2.field_id) / 
                (SELECT COUNT(*) FROM this_template_fields), 1) as sharing_percentage
        FROM this_template_fields ttf
        JOIN document_fields df2 ON ttf.field_id = df2.field_id
        JOIN template_matches tm2 ON df2.document_id = tm2.document_id
        JOIN excel_templates et2 ON tm2.excel_row_id = et2.row_id
        WHERE et2.row_id != $1
        GROUP BY et2.row_id, et2.template_code, et2.stated_complexity
        HAVING COUNT(DISTINCT df2.field_id) > 3
        ORDER BY shared_field_count DESC
        LIMIT 20
      `;
      
      const sharingResult = await pool.query(sharingQuery, [rowId]);
      
      // Calculate complexity evidence breakdown
      const complexityBreakdown = {
        score: template.total_complexity_score || 0,
        components: {
          if_statements: (template.if_statements || 0) * 3,
          nested_if: (template.nested_if_statements || 0) * 2,
          user_input: (template.user_input_fields || 0) * 2,
          calculated: (template.calculated_fields || 0) * 2,
          docvariables: (template.docvariable_fields || 0) * 1,
          mergefields: (template.mergefield_fields || 0) * 1
        },
        evidence: {
          stated: template.stated_complexity,
          calculated: template.complexity_rating,
          validation: template.complexity_validation,
          score_range: getComplexityRange(template.stated_complexity)
        }
      };
      
      res.json({
        template,
        fields: fieldsResult.rows,
        sharingRelationships: sharingResult.rows,
        complexityBreakdown,
        evidence: {
          matchingMethod: template.match_method,
          matchingConfidence: template.match_confidence,
          documentPath: template.document_filename,
          totalFieldsAnalyzed: fieldsResult.rows.length,
          uniqueFieldsEvidence: fieldsResult.rows.filter(f => f.total_template_usage === 1).length,
          sharedFieldsEvidence: fieldsResult.rows.filter(f => f.total_template_usage > 1).length
        }
      });
      
    } catch (error) {
      console.error('Error fetching template details:', error);
      res.status(500).json({ error: 'Failed to fetch template details' });
    }
  });

  // Get paginated templates with search and filtering
  router.get('/templates/browse', async (req, res) => {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const pageSize = parseInt(req.query.pageSize as string) || 20;
      const search = req.query.search as string || '';
      const complexity = req.query.complexity as string || '';
      const matchStatus = req.query.matchStatus as string || '';
      const sortBy = req.query.sortBy as string || 'row_id';
      const sortOrder = req.query.sortOrder as string || 'ASC';
      
      const offset = (page - 1) * pageSize;
      
      let whereConditions = ['1=1'];
      const params: any[] = [];
      let paramCount = 1;
      
      if (search) {
        whereConditions.push(`(et.template_code ILIKE $${paramCount} OR et.description ILIKE $${paramCount})`);
        params.push(`%${search}%`);
        paramCount++;
      }
      
      if (complexity) {
        whereConditions.push(`et.stated_complexity = $${paramCount}`);
        params.push(complexity);
        paramCount++;
      }
      
      if (matchStatus === 'matched') {
        whereConditions.push('tm.document_id IS NOT NULL');
      } else if (matchStatus === 'unmatched') {
        whereConditions.push('tm.document_id IS NULL');
      }
      
      const validSortColumns = ['row_id', 'template_code', 'stated_complexity', 'total_fields', 'reusability_percentage'];
      const sortColumn = validSortColumns.includes(sortBy) ? sortBy : 'row_id';
      const order = sortOrder.toUpperCase() === 'DESC' ? 'DESC' : 'ASC';
      
      const query = `
        WITH template_metrics AS (
          SELECT 
            et.row_id,
            et.template_code,
            et.description,
            et.stated_complexity,
            tm.match_method,
            tm.match_confidence,
            COALESCE(dc.total_fields, 0) as total_fields,
            COALESCE(dc.unique_fields, 0) as unique_fields,
            COALESCE(dc.reusable_fields, 0) as shared_fields,
            CASE 
              WHEN dc.total_fields > 0 
              THEN ROUND(100.0 * dc.reusable_fields / dc.total_fields, 1)
              ELSE 0
            END as reusability_percentage,
            COALESCE(dc.if_statements, 0) as if_statements,
            COALESCE(dc.total_complexity_score, 0) as complexity_score,
            CASE 
              WHEN tm.document_id IS NOT NULL THEN 'Matched'
              ELSE 'Unmatched'
            END as match_status
          FROM excel_templates et
          LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
          LEFT JOIN document_complexity dc ON tm.document_id = dc.document_id
          WHERE ${whereConditions.join(' AND ')}
        )
        SELECT *
        FROM template_metrics
        ORDER BY ${sortColumn} ${order}
        LIMIT $${paramCount} OFFSET $${paramCount + 1}
      `;
      
      params.push(pageSize, offset);
      
      const result = await pool.query(query, params);
      
      // Get total count for pagination
      const countQuery = `
        SELECT COUNT(*) as total
        FROM excel_templates et
        LEFT JOIN template_matches tm ON et.row_id = tm.excel_row_id
        WHERE ${whereConditions.join(' AND ')}
      `;
      
      const countResult = await pool.query(countQuery, params.slice(0, -2));
      const totalCount = parseInt(countResult.rows[0].total);
      const totalPages = Math.ceil(totalCount / pageSize);
      
      res.json({
        templates: result.rows,
        pagination: {
          page,
          pageSize,
          totalCount,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1
        }
      });
      
    } catch (error) {
      console.error('Error browsing templates:', error);
      res.status(500).json({ error: 'Failed to browse templates' });
    }
  });

  // Validate calculations for a specific template
  router.get('/templates/:rowId/validate', async (req, res) => {
    const { rowId } = req.params;
    
    try {
      const validationQuery = `
        WITH field_counts AS (
          -- Count fields directly from document_fields
          SELECT 
            COUNT(DISTINCT f.field_id) as actual_field_count,
            COUNT(DISTINCT CASE WHEN f.field_code LIKE '%DOCVARIABLE%' THEN f.field_id END) as actual_docvar,
            COUNT(DISTINCT CASE WHEN f.field_code LIKE '%MERGEFIELD%' THEN f.field_id END) as actual_merge,
            COUNT(DISTINCT CASE WHEN f.field_code LIKE '%IF %' THEN f.field_id END) as actual_if
          FROM template_matches tm
          JOIN document_fields df ON tm.document_id = df.document_id
          JOIN fields f ON df.field_id = f.field_id
          WHERE tm.excel_row_id = $1
        ),
        stored_counts AS (
          -- Get stored values from document_complexity
          SELECT 
            dc.total_fields as stored_field_count,
            dc.docvariable_fields as stored_docvar,
            dc.mergefield_fields as stored_merge,
            dc.if_statements as stored_if
          FROM template_matches tm
          JOIN document_complexity dc ON tm.document_id = dc.document_id
          WHERE tm.excel_row_id = $1
        )
        SELECT 
          fc.actual_field_count,
          sc.stored_field_count,
          fc.actual_field_count = sc.stored_field_count as fields_match,
          fc.actual_docvar,
          sc.stored_docvar,
          fc.actual_docvar = sc.stored_docvar as docvar_match,
          fc.actual_merge,
          sc.stored_merge,
          fc.actual_merge = sc.stored_merge as merge_match,
          fc.actual_if,
          sc.stored_if,
          fc.actual_if = sc.stored_if as if_match
        FROM field_counts fc, stored_counts sc
      `;
      
      const result = await pool.query(validationQuery, [rowId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Template not found or not matched' });
      }
      
      const validation = result.rows[0];
      const allMatch = validation.fields_match && validation.docvar_match && 
                       validation.merge_match && validation.if_match;
      
      res.json({
        templateId: rowId,
        validation: {
          overall: allMatch ? 'VALID' : 'DISCREPANCY',
          details: validation,
          message: allMatch 
            ? 'All calculations are validated and correct'
            : 'Discrepancies found in calculations - review needed'
        }
      });
      
    } catch (error) {
      console.error('Error validating template:', error);
      res.status(500).json({ error: 'Failed to validate template' });
    }
  });

  return router;
}

function getComplexityRange(complexity: string): string {
  switch (complexity) {
    case 'Simple':
      return '0-10 points';
    case 'Moderate':
      return '11-25 points';
    case 'Complex':
      return '26+ points';
    default:
      return 'Unknown';
  }
}
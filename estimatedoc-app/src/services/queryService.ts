import { documentsData } from '../data/documents';

export interface QueryResult {
  success: boolean;
  data?: any[];
  error?: string;
  rowCount?: number;
  executionTime?: number;
}

export const executeQuery = async (query: string): Promise<QueryResult> => {
  const startTime = performance.now();
  
  try {
    // Parse the query to determine what it's trying to do
    const normalizedQuery = query.toLowerCase().trim();
    
    // For safety, only allow SELECT queries
    if (!normalizedQuery.startsWith('select')) {
      return {
        success: false,
        error: 'Only SELECT queries are allowed for safety reasons'
      };
    }
    
    // Handle different query patterns
    if (normalizedQuery.includes('from documents_complete') || normalizedQuery.includes('from documents')) {
      // Extract document ID if present
      const idMatch = query.match(/where\s+id\s*=\s*(\d+)/i);
      
      if (idMatch) {
        const id = parseInt(idMatch[1]);
        const document = documentsData.find(doc => doc.id === id);
        
        if (document) {
          return {
            success: true,
            data: [document],
            rowCount: 1,
            executionTime: performance.now() - startTime
          };
        } else {
          return {
            success: true,
            data: [],
            rowCount: 0,
            executionTime: performance.now() - startTime
          };
        }
      } else {
        // Return all documents for a general SELECT
        return {
          success: true,
          data: documentsData,
          rowCount: documentsData.length,
          executionTime: performance.now() - startTime
        };
      }
    }
    
    // Handle count queries
    if (normalizedQuery.includes('count(*)')) {
      const whereMatch = query.match(/where\s+(.+?)(?:\s+group\s+by|\s+order\s+by|$)/i);
      
      if (whereMatch) {
        // Parse WHERE conditions
        const condition = whereMatch[1];
        let filteredData = documentsData;
        
        // Handle complexity_level filter
        if (condition.includes('complexity_level')) {
          const levelMatch = condition.match(/complexity_level\s*=\s*['"]([^'"]+)['"]/i);
          if (levelMatch) {
            filteredData = documentsData.filter(doc => 
              doc.complexity.level.toLowerCase() === levelMatch[1].toLowerCase()
            );
          }
        }
        
        return {
          success: true,
          data: [{ count: filteredData.length }],
          rowCount: 1,
          executionTime: performance.now() - startTime
        };
      } else {
        return {
          success: true,
          data: [{ count: documentsData.length }],
          rowCount: 1,
          executionTime: performance.now() - startTime
        };
      }
    }
    
    // Handle aggregation queries
    if (normalizedQuery.includes('sum(') || normalizedQuery.includes('avg(')) {
      let result: any = {};
      
      if (normalizedQuery.includes('sum(effort_calculated)')) {
        result.total_effort = documentsData.reduce((sum, doc) => sum + (doc.effort?.calculated || 0), 0);
      }
      if (normalizedQuery.includes('sum(effort_optimized)')) {
        result.optimized_effort = documentsData.reduce((sum, doc) => sum + (doc.effort?.optimized || 0), 0);
      }
      if (normalizedQuery.includes('avg(total_fields)')) {
        result.avg_fields = documentsData.reduce((sum, doc) => sum + (doc.totals?.allFields || 0), 0) / documentsData.length;
      }
      
      return {
        success: true,
        data: [result],
        rowCount: 1,
        executionTime: performance.now() - startTime
      };
    }
    
    // Default response for unhandled queries
    return {
      success: false,
      error: 'Query pattern not recognized. Supported queries: SELECT * FROM documents, SELECT COUNT(*), aggregations'
    };
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Query execution failed',
      executionTime: performance.now() - startTime
    };
  }
};

// Format query results for display
export const formatQueryResults = (result: QueryResult): string => {
  if (!result.success) {
    return `Error: ${result.error}`;
  }
  
  if (!result.data || result.data.length === 0) {
    return 'No results found';
  }
  
  // For single row results
  if (result.data.length === 1) {
    const row = result.data[0];
    
    // Check if it's a count or aggregation result
    if ('count' in row || 'total_effort' in row || 'avg_fields' in row) {
      return JSON.stringify(row, null, 2);
    }
    
    // For document results, show key fields
    if ('name' in row && 'id' in row) {
      return JSON.stringify({
        id: row.id,
        name: row.name,
        description: row.description,
        totalFields: row.totals?.allFields,
        complexity: row.complexity?.level,
        effort: row.effort?.calculated
      }, null, 2);
    }
  }
  
  // For multiple results, show summary
  return `Found ${result.rowCount} results\n${JSON.stringify(result.data.slice(0, 5), null, 2)}${result.data.length > 5 ? '\n...' : ''}`;
};
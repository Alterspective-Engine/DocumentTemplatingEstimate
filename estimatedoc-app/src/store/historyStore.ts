import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ValueHistory {
  timestamp: number;
  value: number;
  label?: string;
}

export interface DocumentHistory {
  documentId: string;
  documentName: string;
  effort: ValueHistory[];
  optimized: ValueHistory[];
  savings: ValueHistory[];
  complexity: Array<{ timestamp: number; value: string }>;
  fields: ValueHistory[];
}

interface HistoryStore {
  // Document-specific histories
  documentHistories: Map<string, DocumentHistory>;
  
  // Global metrics history
  globalHistory: {
    totalEffort: ValueHistory[];
    totalOptimized: ValueHistory[];
    totalSavings: ValueHistory[];
    averageReusability: ValueHistory[];
    documentCount: ValueHistory[];
  };
  
  // Settings to track how many history points to keep
  maxHistoryPoints: number;
  
  // Actions
  recordDocumentChange: (
    documentId: string,
    documentName: string,
    values: {
      effort: number;
      optimized: number;
      savings: number;
      complexity: string;
      fields: number;
    }
  ) => void;
  
  recordGlobalChange: (values: {
    totalEffort: number;
    totalOptimized: number;
    totalSavings: number;
    averageReusability: number;
    documentCount: number;
  }) => void;
  
  getDocumentHistory: (documentId: string) => DocumentHistory | undefined;
  getRecentChange: (documentId: string, field: keyof DocumentHistory) => {
    current: number;
    previous: number;
    change: number;
    changePercent: number;
    trend: 'up' | 'down' | 'stable';
  } | null;
  
  clearHistory: () => void;
  clearDocumentHistory: (documentId: string) => void;
}

const MAX_HISTORY_POINTS = 20;

export const useHistoryStore = create<HistoryStore>()(
  persist(
    (set, get) => ({
      documentHistories: new Map(),
      globalHistory: {
        totalEffort: [],
        totalOptimized: [],
        totalSavings: [],
        averageReusability: [],
        documentCount: []
      },
      maxHistoryPoints: MAX_HISTORY_POINTS,
      
      recordDocumentChange: (documentId, documentName, values) => {
        const { documentHistories, maxHistoryPoints } = get();
        const timestamp = Date.now();
        
        // Get or create document history
        let docHistory = documentHistories.get(documentId);
        if (!docHistory) {
          docHistory = {
            documentId,
            documentName,
            effort: [],
            optimized: [],
            savings: [],
            complexity: [],
            fields: []
          };
        }
        
        // Add new values
        docHistory.effort.push({ timestamp, value: values.effort });
        docHistory.optimized.push({ timestamp, value: values.optimized });
        docHistory.savings.push({ timestamp, value: values.savings });
        docHistory.complexity.push({ timestamp, value: values.complexity });
        docHistory.fields.push({ timestamp, value: values.fields });
        
        // Trim to max history points
        if (docHistory.effort.length > maxHistoryPoints) {
          docHistory.effort = docHistory.effort.slice(-maxHistoryPoints);
          docHistory.optimized = docHistory.optimized.slice(-maxHistoryPoints);
          docHistory.savings = docHistory.savings.slice(-maxHistoryPoints);
          docHistory.complexity = docHistory.complexity.slice(-maxHistoryPoints);
          docHistory.fields = docHistory.fields.slice(-maxHistoryPoints);
        }
        
        // Update the map
        const newHistories = new Map(documentHistories);
        newHistories.set(documentId, docHistory);
        
        set({ documentHistories: newHistories });
      },
      
      recordGlobalChange: (values) => {
        const { globalHistory, maxHistoryPoints } = get();
        const timestamp = Date.now();
        
        // Add new values
        const newHistory = {
          totalEffort: [...globalHistory.totalEffort, { timestamp, value: values.totalEffort }],
          totalOptimized: [...globalHistory.totalOptimized, { timestamp, value: values.totalOptimized }],
          totalSavings: [...globalHistory.totalSavings, { timestamp, value: values.totalSavings }],
          averageReusability: [...globalHistory.averageReusability, { timestamp, value: values.averageReusability }],
          documentCount: [...globalHistory.documentCount, { timestamp, value: values.documentCount }]
        };
        
        // Trim to max history points
        Object.keys(newHistory).forEach(key => {
          const k = key as keyof typeof newHistory;
          if (newHistory[k].length > maxHistoryPoints) {
            newHistory[k] = newHistory[k].slice(-maxHistoryPoints);
          }
        });
        
        set({ globalHistory: newHistory });
      },
      
      getDocumentHistory: (documentId) => {
        return get().documentHistories.get(documentId);
      },
      
      getRecentChange: (documentId, field) => {
        const docHistory = get().documentHistories.get(documentId);
        if (!docHistory) return null;
        
        const fieldHistory = docHistory[field] as ValueHistory[];
        if (!fieldHistory || fieldHistory.length < 2) return null;
        
        const current = fieldHistory[fieldHistory.length - 1].value;
        const previous = fieldHistory[fieldHistory.length - 2].value;
        const change = current - previous;
        const changePercent = previous !== 0 ? (change / previous) * 100 : 0;
        
        return {
          current,
          previous,
          change,
          changePercent,
          trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable'
        };
      },
      
      clearHistory: () => {
        set({
          documentHistories: new Map(),
          globalHistory: {
            totalEffort: [],
            totalOptimized: [],
            totalSavings: [],
            averageReusability: [],
            documentCount: []
          }
        });
      },
      
      clearDocumentHistory: (documentId) => {
        const { documentHistories } = get();
        const newHistories = new Map(documentHistories);
        newHistories.delete(documentId);
        set({ documentHistories: newHistories });
      }
    }),
    {
      name: 'estimatedoc-history',
      partialize: (state) => ({
        globalHistory: state.globalHistory,
        // Only persist last 5 history points per document to save space
        documentHistories: Array.from(state.documentHistories.entries()).reduce((acc, [id, history]) => {
          acc.set(id, {
            ...history,
            effort: history.effort.slice(-5),
            optimized: history.optimized.slice(-5),
            savings: history.savings.slice(-5),
            complexity: history.complexity.slice(-5),
            fields: history.fields.slice(-5)
          });
          return acc;
        }, new Map())
      })
    }
  )
);
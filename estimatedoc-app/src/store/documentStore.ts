import { create } from 'zustand';
import type { Document } from '../types/document.types';
import type { CalculatorSettings } from '../types/calculator.types';
import { documentsData } from '../data/documents';
import databaseDocuments from '../data/database-documents';
import sqlDocuments from '../data/sql-documents';
import { useCalculatorStore } from './calculatorStore';
import { useHistoryStore } from './historyStore';
import dataSourceConfig from '../config/data-source';

interface DocumentFilter {
  complexity?: 'Simple' | 'Moderate' | 'Complex' | null;
  source?: 'SQL' | 'Estimated' | null;
  searchTerm?: string;
  minFields?: number;
  maxFields?: number;
  hasScripts?: boolean;
}

interface DocumentSort {
  field: 'name' | 'complexity' | 'effort' | 'fields' | 'reusability';
  direction: 'asc' | 'desc';
}

interface DocumentStore {
  documents: Document[];
  filteredDocuments: Document[];
  selectedDocument: Document | null;
  filter: DocumentFilter;
  sort: DocumentSort;
  isRecalculating: boolean;
  recalculationProgress: number;
  updatingDocuments: Set<string>;
  dataSource: 'SQL' | 'database' | 'hardcoded';
  
  // Actions
  setSelectedDocument: (document: Document | null) => void;
  setFilter: (filter: DocumentFilter) => void;
  setSort: (sort: DocumentSort) => void;
  applyFiltersAndSort: () => void;
  recalculateAllDocuments: (settings: CalculatorSettings) => void;
  recalculateAllDocumentsLive: (settings: CalculatorSettings) => Promise<void>;
  reloadDataFromSQL: () => Promise<void>;
  
  // Statistics
  getStatistics: () => {
    total: number;
    byComplexity: Record<string, number>;
    totalEffort: number;
    totalOptimizedEffort: number;
    averageReusability: number;
  };
}

// Initialize documents with calculated values
const initializeDocuments = (): { documents: Document[], source: 'SQL' | 'database' | 'hardcoded' } => {
  const calculatorStore = useCalculatorStore.getState();
  const settings = calculatorStore.settings;
  
  try {
    // Priority: 1. SQL JSON exports, 2. Database documents, 3. Hardcoded data
    // Note: SQLite cannot run in browser, only use JSON data
    let documentsToUse: Document[] = [];
    let source: 'SQL' | 'database' | 'hardcoded' = 'SQL';
    
    // Use SQL JSON exports as primary source
    if (sqlDocuments && sqlDocuments.length > 0) {
      console.log(`📊 Loading ${sqlDocuments.length} documents from SQL JSON exports`);
      documentsToUse = sqlDocuments;
      source = 'SQL';
    } else {
      console.log('⚠️ SQL documents not available, falling back to database documents');
      const useDatabase = dataSourceConfig.type === 'database' || dataSourceConfig.useDatabaseIfAvailable;
      documentsToUse = useDatabase ? databaseDocuments : documentsData;
      source = useDatabase ? 'database' : 'hardcoded';
    }
    
    console.log(`✅ Loaded ${documentsToUse.length} documents from ${source} source`);
    
    // Calculate all documents with current settings
    const documents = documentsToUse.map(doc => {
      return calculatorStore.recalculateDocument(doc, settings);
    });
    
    return { documents, source };
  } catch (error) {
    console.error('❌ Error initializing documents:', error);
    // Final fallback to hardcoded data
    const documents = documentsData.map(doc => {
      return calculatorStore.recalculateDocument(doc, settings);
    });
    return { documents, source: 'hardcoded' };
  }
};

export const useDocumentStore = create<DocumentStore>((set, get) => {
  // Initialize with calculated documents
  const { documents: initialDocs, source } = initializeDocuments();
  
  return {
    documents: initialDocs,
    filteredDocuments: initialDocs,
    selectedDocument: null,
    filter: {},
    sort: { field: 'name', direction: 'asc' },
    isRecalculating: false,
    recalculationProgress: 0,
    updatingDocuments: new Set(),
    dataSource: source,
  
  setSelectedDocument: (document) => set({ selectedDocument: document }),
  
  setFilter: (filter) => {
    set({ filter });
    get().applyFiltersAndSort();
  },
  
  setSort: (sort) => {
    set({ sort });
    get().applyFiltersAndSort();
  },
  
  applyFiltersAndSort: () => {
    const { documents, filter, sort } = get();
    
    // Apply filters
    let filtered = [...documents];
    
    if (filter.complexity) {
      filtered = filtered.filter(doc => {
        const complexity = (doc.complexity as any)?.level || doc.complexity || 'simple';
        return complexity === filter.complexity;
      });
    }
    
    if (filter.source) {
      filtered = filtered.filter(doc => doc.evidence.source === filter.source);
    }
    
    if (filter.searchTerm) {
      const term = filter.searchTerm.toLowerCase();
      filtered = filtered.filter(doc => 
        doc.name.toLowerCase().includes(term) ||
        doc.description.toLowerCase().includes(term)
      );
    }
    
    if (filter.minFields !== undefined) {
      filtered = filtered.filter(doc => {
        const fieldCount = doc.totals?.allFields || 
                          (typeof doc.fields === 'number' ? doc.fields : 0) ||
                          (doc.fieldTypes ? Object.values(doc.fieldTypes).reduce((sum: number, val) => sum + (val as number), 0) : 0);
        return fieldCount >= filter.minFields!;
      });
    }
    
    if (filter.maxFields !== undefined) {
      filtered = filtered.filter(doc => {
        const fieldCount = doc.totals?.allFields || 
                          (typeof doc.fields === 'number' ? doc.fields : 0) ||
                          (doc.fieldTypes ? Object.values(doc.fieldTypes).reduce((sum: number, val) => sum + (val as number), 0) : 0);
        return fieldCount <= filter.maxFields!;
      });
    }
    
    if (filter.hasScripts !== undefined) {
      filtered = filtered.filter(doc => {
        let scriptCount = 0;
        if (doc.fields && typeof doc.fields === 'object' && 'precedentScript' in doc.fields) {
          scriptCount = (doc.fields as any).precedentScript.count + 
                       (doc.fields as any).builtInScript.count + 
                       (doc.fields as any).scripted.count;
        } else if (doc.fieldTypes) {
          scriptCount = (doc.fieldTypes.precedentScript || 0) + 
                       (doc.fieldTypes.builtInScript || 0) + 
                       (doc.fieldTypes.scripted || 0);
        }
        return filter.hasScripts ? scriptCount > 0 : scriptCount === 0;
      });
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      let compareValue = 0;
      
      switch (sort.field) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;
        case 'complexity':
          const complexityOrder = { 'Simple': 1, 'Moderate': 2, 'Complex': 3 };
          const aComplexity = (a.complexity as any)?.level || a.complexity || 'Simple';
          const bComplexity = (b.complexity as any)?.level || b.complexity || 'Simple';
          compareValue = (complexityOrder[aComplexity as keyof typeof complexityOrder] || 1) - (complexityOrder[bComplexity as keyof typeof complexityOrder] || 1);
          break;
        case 'effort':
          compareValue = (a.effort?.calculated || a.effort?.base || 0) - (b.effort?.calculated || b.effort?.base || 0);
          break;
        case 'fields':
          const aFields = a.totals?.allFields || 
                         (typeof a.fields === 'number' ? a.fields : 0) ||
                         (a.fieldTypes ? Object.values(a.fieldTypes).reduce((sum: number, val) => sum + (val as number), 0) : 0);
          const bFields = b.totals?.allFields || 
                         (typeof b.fields === 'number' ? b.fields : 0) ||
                         (b.fieldTypes ? Object.values(b.fieldTypes).reduce((sum: number, val) => sum + (val as number), 0) : 0);
          compareValue = aFields - bFields;
          break;
        case 'reusability':
          const aReuse = a.totals?.reuseRate ? parseFloat(a.totals.reuseRate) : (a.reusability || 0);
          const bReuse = b.totals?.reuseRate ? parseFloat(b.totals.reuseRate) : (b.reusability || 0);
          compareValue = aReuse - bReuse;
          break;
      }
      
      return sort.direction === 'asc' ? compareValue : -compareValue;
    });
    
    set({ filteredDocuments: filtered });
  },
  
  recalculateAllDocuments: (settings) => {
    const { documents } = get();
    const calculatorStore = useCalculatorStore.getState();
    const historyStore = useHistoryStore.getState();
    
    // Record history for each document
    documents.forEach(doc => {
      historyStore.recordDocumentChange(doc.id.toString(), doc.name, {
        effort: doc.effort?.calculated || 0,
        optimized: doc.effort?.optimized || 0,
        savings: doc.effort?.savings || 0,
        complexity: (doc.complexity as any)?.level || doc.complexity || 'simple',
        fields: doc.totals?.allFields || 0
      });
    });
    
    // Use the calculator store's calculation method for consistency
    const recalculatedDocs = documents.map(doc => {
      return calculatorStore.recalculateDocument(doc, settings);
    });
    
    // Record global history
    const stats = get().getStatistics();
    historyStore.recordGlobalChange({
      totalEffort: stats.totalEffort,
      totalOptimized: stats.totalOptimizedEffort,
      totalSavings: stats.totalEffort - stats.totalOptimizedEffort,
      averageReusability: stats.averageReusability,
      documentCount: stats.total
    });
    
    set({ documents: recalculatedDocs });
    get().applyFiltersAndSort();
  },
  
  recalculateAllDocumentsLive: async (settings) => {
    const { documents } = get();
    const calculatorStore = useCalculatorStore.getState();
    const historyStore = useHistoryStore.getState();
    const batchSize = 20; // Process in batches for smooth animation
    
    set({ isRecalculating: true, recalculationProgress: 0, updatingDocuments: new Set() });
    
    // Record current state to history
    documents.forEach(doc => {
      historyStore.recordDocumentChange(doc.id.toString(), doc.name, {
        effort: doc.effort?.calculated || 0,
        optimized: doc.effort?.optimized || 0,
        savings: doc.effort?.savings || 0,
        complexity: (doc.complexity as any)?.level || doc.complexity || 'simple',
        fields: doc.totals?.allFields || 0
      });
    });
    
    const recalculatedDocs = [...documents];
    
    for (let i = 0; i < documents.length; i += batchSize) {
      const batch = documents.slice(i, i + batchSize);
      const updatingIds = new Set(batch.map(d => d.id.toString()));
      
      // Mark documents as updating
      set({ updatingDocuments: updatingIds });
      
      // Animate the update
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Recalculate batch
      batch.forEach((doc, index) => {
        const globalIndex = i + index;
        recalculatedDocs[globalIndex] = calculatorStore.recalculateDocument(doc, settings);
      });
      
      // Update progress
      const progress = Math.min(100, ((i + batchSize) / documents.length) * 100);
      set({ 
        documents: recalculatedDocs,
        recalculationProgress: progress,
        updatingDocuments: new Set()
      });
      
      // Apply filters after each batch
      get().applyFiltersAndSort();
      
      // Small delay for visual effect
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    // Record new global history
    const stats = get().getStatistics();
    historyStore.recordGlobalChange({
      totalEffort: stats.totalEffort,
      totalOptimized: stats.totalOptimizedEffort,
      totalSavings: stats.totalEffort - stats.totalOptimizedEffort,
      averageReusability: stats.averageReusability,
      documentCount: stats.total
    });
    
    set({ 
      isRecalculating: false, 
      recalculationProgress: 100,
      updatingDocuments: new Set()
    });
    
    // Clear progress after animation
    setTimeout(() => {
      set({ recalculationProgress: 0 });
    }, 500);
  },
  
  reloadDataFromSQL: async () => {
    console.log('🔄 Reloading data from SQL...');
    set({ isRecalculating: true, recalculationProgress: 0 });
    
    try {
      // Re-run the process-sql-data script (this would be done server-side in production)
      // For now, we'll just reload the documents
      const { documents: newDocs, source } = initializeDocuments();
      
      set({ 
        documents: newDocs,
        filteredDocuments: newDocs,
        dataSource: source,
        isRecalculating: false,
        recalculationProgress: 100
      });
      
      get().applyFiltersAndSort();
      
      console.log(`✅ Reloaded ${newDocs.length} documents from ${source} source`);
      
      // Clear progress after animation
      setTimeout(() => {
        set({ recalculationProgress: 0 });
      }, 500);
    } catch (error) {
      console.error('❌ Error reloading data:', error);
      set({ isRecalculating: false, recalculationProgress: 0 });
    }
  },
  
  getStatistics: () => {
    const { filteredDocuments } = get();
    
    const byComplexity = filteredDocuments.reduce((acc, doc) => {
      const complexity = (doc.complexity as any)?.level || doc.complexity || 'simple';
      acc[complexity] = (acc[complexity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const totalEffort = filteredDocuments.reduce((sum, doc) => sum + (doc.effort?.calculated || 0), 0);
    const totalOptimizedEffort = filteredDocuments.reduce((sum, doc) => sum + (doc.effort?.optimized || 0), 0);
    
    const totalReusability = filteredDocuments.reduce((sum, doc) => {
      return sum + parseFloat(String(doc.totals?.reuseRate || '0'));
    }, 0);
    
    return {
      total: filteredDocuments.length,
      byComplexity,
      totalEffort,
      totalOptimizedEffort,
      averageReusability: totalReusability / filteredDocuments.length
    };
  }
  };
});
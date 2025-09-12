import { create } from 'zustand';
import type { Document } from '../types/document.types';
import type { CalculatorSettings } from '../types/calculator.types';
import { documentsData } from '../data/documents';
import { useCalculatorStore } from './calculatorStore';
import { useHistoryStore } from './historyStore';

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
  
  // Actions
  setSelectedDocument: (document: Document | null) => void;
  setFilter: (filter: DocumentFilter) => void;
  setSort: (sort: DocumentSort) => void;
  applyFiltersAndSort: () => void;
  recalculateAllDocuments: (settings: CalculatorSettings) => void;
  recalculateAllDocumentsLive: (settings: CalculatorSettings) => Promise<void>;
  
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
const initializeDocuments = () => {
  const calculatorStore = useCalculatorStore.getState();
  const settings = calculatorStore.settings;
  
  // Calculate all documents with current settings
  return documentsData.map(doc => {
    return calculatorStore.recalculateDocument(doc, settings);
  });
};

export const useDocumentStore = create<DocumentStore>((set, get) => {
  // Initialize with calculated documents
  const initialDocs = initializeDocuments();
  
  return {
    documents: initialDocs,
    filteredDocuments: initialDocs,
    selectedDocument: null,
    filter: {},
    sort: { field: 'name', direction: 'asc' },
    isRecalculating: false,
    recalculationProgress: 0,
    updatingDocuments: new Set(),
  
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
      filtered = filtered.filter(doc => doc.complexity.level === filter.complexity);
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
      filtered = filtered.filter(doc => doc.totals.allFields >= filter.minFields!);
    }
    
    if (filter.maxFields !== undefined) {
      filtered = filtered.filter(doc => doc.totals.allFields <= filter.maxFields!);
    }
    
    if (filter.hasScripts !== undefined) {
      filtered = filtered.filter(doc => {
        const scriptCount = doc.fields.precedentScript.count + 
                          doc.fields.builtInScript.count + 
                          doc.fields.scripted.count;
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
          compareValue = complexityOrder[a.complexity.level] - complexityOrder[b.complexity.level];
          break;
        case 'effort':
          compareValue = a.effort.calculated - b.effort.calculated;
          break;
        case 'fields':
          compareValue = a.totals.allFields - b.totals.allFields;
          break;
        case 'reusability':
          const aReuse = parseFloat(a.totals.reuseRate);
          const bReuse = parseFloat(b.totals.reuseRate);
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
      historyStore.recordDocumentChange(doc.id, doc.name, {
        effort: doc.effort.calculated,
        optimized: doc.effort.optimized,
        savings: doc.effort.savings,
        complexity: doc.complexity.level,
        fields: doc.totals.allFields
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
      historyStore.recordDocumentChange(doc.id, doc.name, {
        effort: doc.effort.calculated,
        optimized: doc.effort.optimized,
        savings: doc.effort.savings,
        complexity: doc.complexity.level,
        fields: doc.totals.allFields
      });
    });
    
    const recalculatedDocs = [...documents];
    const totalBatches = Math.ceil(documents.length / batchSize);
    
    for (let i = 0; i < documents.length; i += batchSize) {
      const batch = documents.slice(i, i + batchSize);
      const updatingIds = new Set(batch.map(d => d.id));
      
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
  
  getStatistics: () => {
    const { filteredDocuments } = get();
    
    const byComplexity = filteredDocuments.reduce((acc, doc) => {
      acc[doc.complexity.level] = (acc[doc.complexity.level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const totalEffort = filteredDocuments.reduce((sum, doc) => sum + doc.effort.calculated, 0);
    const totalOptimizedEffort = filteredDocuments.reduce((sum, doc) => sum + doc.effort.optimized, 0);
    
    const totalReusability = filteredDocuments.reduce((sum, doc) => {
      return sum + parseFloat(doc.totals.reuseRate);
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
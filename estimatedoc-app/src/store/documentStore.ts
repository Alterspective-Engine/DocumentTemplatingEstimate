import { create } from 'zustand';
import type { Document } from '../types/document.types';
import type { CalculatorSettings } from '../types/calculator.types';
import { documentsData } from '../data/documents';

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
  
  // Actions
  setSelectedDocument: (document: Document | null) => void;
  setFilter: (filter: DocumentFilter) => void;
  setSort: (sort: DocumentSort) => void;
  applyFiltersAndSort: () => void;
  recalculateAllDocuments: (settings: CalculatorSettings) => void;
  
  // Statistics
  getStatistics: () => {
    total: number;
    byComplexity: Record<string, number>;
    totalEffort: number;
    totalOptimizedEffort: number;
    averageReusability: number;
  };
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  documents: documentsData,
  filteredDocuments: documentsData,
  selectedDocument: null,
  filter: {},
  sort: { field: 'name', direction: 'asc' },
  
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
    
    // Recalculate all documents with new settings
    const recalculatedDocs = documents.map(doc => {
      // Calculate total time based on field counts and current settings
      const fieldTime = 
        doc.fields.if.count * (settings.fieldTimeEstimates.ifStatement.current / 60) +
        doc.fields.precedentScript.count * (settings.fieldTimeEstimates.precedentScript.current / 60) +
        doc.fields.reflection.count * (settings.fieldTimeEstimates.reflection.current / 60) +
        doc.fields.search.count * (settings.fieldTimeEstimates.search.current / 60) +
        doc.fields.unbound.count * (settings.fieldTimeEstimates.unbound.current / 60) +
        doc.fields.builtInScript.count * (settings.fieldTimeEstimates.builtInScript.current / 60) +
        doc.fields.extended.count * (settings.fieldTimeEstimates.extended.current / 60) +
        doc.fields.scripted.count * (settings.fieldTimeEstimates.scripted.current / 60);
      
      // Determine complexity based on current thresholds
      const totalFields = doc.totals.allFields;
      const totalScripts = doc.fields.precedentScript.count + 
                          doc.fields.builtInScript.count + 
                          doc.fields.scripted.count;
      const ifStatements = doc.fields.if.count;
      
      let complexity: 'Simple' | 'Moderate' | 'Complex';
      let complexityReason: string;
      
      if (totalFields < settings.complexityThresholds.simple.maxFields &&
          totalScripts <= settings.complexityThresholds.simple.maxScripts &&
          ifStatements <= settings.complexityThresholds.simple.maxIfStatements) {
        complexity = 'Simple';
        complexityReason = `<${settings.complexityThresholds.simple.maxFields} fields, ≤${settings.complexityThresholds.simple.maxScripts} scripts, ≤${settings.complexityThresholds.simple.maxIfStatements} IFs`;
      } else if (totalFields >= settings.complexityThresholds.moderate.minFields &&
                 totalFields <= settings.complexityThresholds.moderate.maxFields &&
                 totalScripts < settings.complexityThresholds.moderate.maxScripts &&
                 ifStatements <= settings.complexityThresholds.moderate.maxIfStatements) {
        complexity = 'Moderate';
        complexityReason = `${settings.complexityThresholds.moderate.minFields}-${settings.complexityThresholds.moderate.maxFields} fields, <${settings.complexityThresholds.moderate.maxScripts} scripts, ≤${settings.complexityThresholds.moderate.maxIfStatements} IFs`;
      } else {
        complexity = 'Complex';
        complexityReason = `Exceeds moderate thresholds`;
      }
      
      // Apply complexity multiplier
      const multiplier = settings.complexityMultipliers[complexity.toLowerCase() as 'simple' | 'moderate' | 'complex'].current;
      const calculatedHours = fieldTime * multiplier;
      
      // Calculate optimization
      const reuseRate = parseFloat(doc.totals.reuseRate) / 100;
      const optimizationFactor = settings.optimization.reuseEfficiency.current / 100;
      const savings = calculatedHours * reuseRate * optimizationFactor;
      const optimizedHours = calculatedHours - savings;
      
      // Return updated document
      return {
        ...doc,
        complexity: {
          ...doc.complexity,
          level: complexity,
          reason: complexityReason
        },
        effort: {
          ...doc.effort,
          calculated: calculatedHours,
          optimized: optimizedHours,
          savings
        }
      };
    });
    
    set({ documents: recalculatedDocs });
    get().applyFiltersAndSort();
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
}));
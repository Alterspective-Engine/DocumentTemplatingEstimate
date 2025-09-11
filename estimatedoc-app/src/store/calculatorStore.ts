import { create } from 'zustand';
import type { CalculatorSettings } from '../types/calculator.types';
import type { Document } from '../types/document.types';
import { useDocumentStore } from './documentStore';

interface CalculatorStore {
  settings: CalculatorSettings;
  isOpen: boolean;
  originalSettings: CalculatorSettings | null;
  previewActive: boolean;
  previewImpact: {
    totalDocuments: number;
    totalHoursBefore: number;
    totalHoursAfter: number;
    totalSavings: number;
    percentChange: number;
  } | null;
  
  // Actions
  openCalculator: () => void;
  closeCalculator: () => void;
  updateFieldTime: (field: keyof CalculatorSettings['fieldTimeEstimates'], value: number) => void;
  updateComplexityThreshold: (complexity: 'simple' | 'moderate', field: string, value: number) => void;
  updateComplexityMultiplier: (complexity: 'simple' | 'moderate' | 'complex', value: number) => void;
  updateOptimization: (field: keyof CalculatorSettings['optimization'], value: number) => void;
  resetToDefaults: () => void;
  applySettings: () => void;
  calculatePreviewImpact: () => void;
  
  // Calculations
  recalculateDocument: (document: Document, customSettings?: CalculatorSettings | null) => Document;
}

const defaultSettings: CalculatorSettings = {
  fieldTimeEstimates: {
    ifStatement: { min: 5, default: 15, max: 60, current: 15, unit: 'minutes' },
    precedentScript: { min: 10, default: 30, max: 120, current: 30, unit: 'minutes' },
    reflection: { min: 2, default: 5, max: 30, current: 5, unit: 'minutes' },
    search: { min: 5, default: 10, max: 45, current: 10, unit: 'minutes' },
    unbound: { min: 2, default: 5, max: 20, current: 5, unit: 'minutes' },
    builtInScript: { min: 5, default: 15, max: 60, current: 15, unit: 'minutes' },
    extended: { min: 5, default: 10, max: 40, current: 10, unit: 'minutes' },
    scripted: { min: 10, default: 20, max: 90, current: 20, unit: 'minutes' }
  },
  complexityThresholds: {
    simple: {
      maxFields: 10,
      maxScripts: 0,
      maxIfStatements: 2
    },
    moderate: {
      minFields: 10,
      maxFields: 20,
      maxScripts: 5,
      maxIfStatements: 20
    }
  },
  complexityMultipliers: {
    simple: { min: 0.5, default: 1.0, max: 1.5, current: 1.0 },
    moderate: { min: 1.0, default: 1.5, max: 2.5, current: 1.5 },
    complex: { min: 2.0, default: 2.5, max: 5.0, current: 2.5 }
  },
  optimization: {
    reuseEfficiency: { min: 0, default: 40, max: 80, current: 40, unit: '%' },
    learningCurve: { min: 0, default: 10, max: 30, current: 10, unit: '%' },
    automationPotential: { min: 0, default: 20, max: 50, current: 20, unit: '%' }
  },
  confidence: {
    sqlDataWeight: 1.0,
    estimatedDataWeight: 0.7,
    showConfidenceIntervals: true
  }
};

export const useCalculatorStore = create<CalculatorStore>((set, get) => ({
  settings: defaultSettings,
  isOpen: false,
  originalSettings: null,
  previewActive: false,
  previewImpact: null,
  
  openCalculator: () => set({ 
    isOpen: true, 
    originalSettings: get().settings,
    previewActive: true
  }),
  closeCalculator: () => set({ 
    isOpen: false, 
    originalSettings: null,
    previewActive: false,
    previewImpact: null
  }),
  
  updateFieldTime: (field, value) => {
    const { settings } = get();
    set({
      settings: {
        ...settings,
        fieldTimeEstimates: {
          ...settings.fieldTimeEstimates,
          [field]: {
            ...settings.fieldTimeEstimates[field],
            current: value
          }
        }
      }
    });
    // Trigger preview calculation
    get().calculatePreviewImpact();
  },
  
  updateComplexityThreshold: (complexity, field, value) => {
    const { settings } = get();
    set({
      settings: {
        ...settings,
        complexityThresholds: {
          ...settings.complexityThresholds,
          [complexity]: {
            ...settings.complexityThresholds[complexity],
            [field]: value
          }
        }
      }
    });
    // Trigger preview calculation
    get().calculatePreviewImpact();
  },
  
  updateComplexityMultiplier: (complexity, value) => {
    const { settings } = get();
    set({
      settings: {
        ...settings,
        complexityMultipliers: {
          ...settings.complexityMultipliers,
          [complexity]: {
            ...settings.complexityMultipliers[complexity],
            current: value
          }
        }
      }
    });
    // Trigger preview calculation
    get().calculatePreviewImpact();
  },
  
  updateOptimization: (field, value) => {
    const { settings } = get();
    set({
      settings: {
        ...settings,
        optimization: {
          ...settings.optimization,
          [field]: {
            ...settings.optimization[field],
            current: value
          }
        }
      }
    });
    // Trigger preview calculation
    get().calculatePreviewImpact();
  },
  
  resetToDefaults: () => set({ settings: defaultSettings }),
  
  applySettings: () => {
    const { settings } = get();
    set({ originalSettings: settings, previewActive: false, previewImpact: null });
    
    // Trigger live recalculation of all documents
    const documentStore = useDocumentStore.getState();
    documentStore.recalculateAllDocuments(settings);
  },
  
  calculatePreviewImpact: () => {
    const { settings, originalSettings } = get();
    
    if (!originalSettings) {
      set({ previewImpact: null });
      return;
    }
    
    // Get all documents from document store
    const documentStore = useDocumentStore.getState();
    const documents = documentStore.documents;
    
    // Calculate total hours with original settings
    let totalHoursBefore = 0;
    let totalHoursAfter = 0;
    
    documents.forEach(doc => {
      // Calculate with original settings
      const originalDoc = get().recalculateDocument(doc, originalSettings);
      totalHoursBefore += originalDoc.effort.optimized;
      
      // Calculate with new settings  
      const newDoc = get().recalculateDocument(doc, settings);
      totalHoursAfter += newDoc.effort.optimized;
    });
    
    const totalSavings = totalHoursBefore - totalHoursAfter;
    const percentChange = totalHoursBefore > 0 
      ? ((totalHoursAfter - totalHoursBefore) / totalHoursBefore) * 100 
      : 0;
    
    set({
      previewImpact: {
        totalDocuments: documents.length,
        totalHoursBefore: Math.round(totalHoursBefore),
        totalHoursAfter: Math.round(totalHoursAfter),
        totalSavings: Math.round(totalSavings),
        percentChange: Math.round(percentChange * 10) / 10
      }
    });
  },
  
  recalculateDocument: (document, customSettings = null) => {
    const settings = customSettings || get().settings;
    
    // Calculate total time based on field counts and current settings
    const fieldTime = 
      document.fields.if.count * (settings.fieldTimeEstimates.ifStatement.current / 60) +
      document.fields.precedentScript.count * (settings.fieldTimeEstimates.precedentScript.current / 60) +
      document.fields.reflection.count * (settings.fieldTimeEstimates.reflection.current / 60) +
      document.fields.search.count * (settings.fieldTimeEstimates.search.current / 60) +
      document.fields.unbound.count * (settings.fieldTimeEstimates.unbound.current / 60) +
      document.fields.builtInScript.count * (settings.fieldTimeEstimates.builtInScript.current / 60) +
      document.fields.extended.count * (settings.fieldTimeEstimates.extended.current / 60) +
      document.fields.scripted.count * (settings.fieldTimeEstimates.scripted.current / 60);
    
    // Determine complexity based on current thresholds
    const totalFields = document.totals.allFields;
    const totalScripts = document.fields.precedentScript.count + 
                        document.fields.builtInScript.count + 
                        document.fields.scripted.count;
    const ifStatements = document.fields.if.count;
    
    let complexity: 'Simple' | 'Moderate' | 'Complex';
    let complexityReason: string;
    
    if (totalFields < settings.complexityThresholds.simple.maxFields &&
        totalScripts <= settings.complexityThresholds.simple.maxScripts &&
        ifStatements <= settings.complexityThresholds.simple.maxIfStatements) {
      complexity = 'Simple';
      complexityReason = `<${settings.complexityThresholds.simple.maxFields} fields (${totalFields}), ≤${settings.complexityThresholds.simple.maxScripts} scripts, ≤${settings.complexityThresholds.simple.maxIfStatements} IFs`;
    } else if (totalFields >= settings.complexityThresholds.moderate.minFields &&
               totalFields <= settings.complexityThresholds.moderate.maxFields &&
               totalScripts < settings.complexityThresholds.moderate.maxScripts &&
               ifStatements <= settings.complexityThresholds.moderate.maxIfStatements) {
      complexity = 'Moderate';
      complexityReason = `${settings.complexityThresholds.moderate.minFields}-${settings.complexityThresholds.moderate.maxFields} fields (${totalFields}), <${settings.complexityThresholds.moderate.maxScripts} scripts, ≤${settings.complexityThresholds.moderate.maxIfStatements} IFs`;
    } else {
      complexity = 'Complex';
      complexityReason = `Exceeds moderate thresholds`;
    }
    
    // Apply complexity multiplier
    const multiplier = settings.complexityMultipliers[complexity.toLowerCase() as 'simple' | 'moderate' | 'complex'].current;
    const calculatedHours = fieldTime * multiplier;
    
    // Calculate optimization
    const reuseRate = parseFloat(document.totals.reuseRate) / 100;
    const optimizationFactor = settings.optimization.reuseEfficiency.current / 100;
    const savings = calculatedHours * reuseRate * optimizationFactor;
    const optimizedHours = calculatedHours - savings;
    
    // Return updated document
    return {
      ...document,
      complexity: {
        level: complexity,
        reason: complexityReason,
        calculation: {
          formula: "Field_Time × Complexity_Multiplier",
          inputs: {
            fieldTime,
            multiplier
          },
          steps: [
            { label: "Field Time", value: fieldTime },
            { label: "Complexity", value: complexity },
            { label: "Multiplier", value: multiplier },
            { label: "Final Hours", value: calculatedHours }
          ],
          result: calculatedHours
        }
      },
      effort: {
        calculated: calculatedHours,
        optimized: optimizedHours,
        savings,
        calculation: {
          formula: "Calculated_Hours - (Calculated_Hours × Reuse_Rate × Optimization_Factor)",
          inputs: {
            calculatedHours,
            reuseRate,
            optimizationFactor
          },
          steps: [
            { label: "Base Hours", value: calculatedHours },
            { label: "Reuse Rate", value: `${(reuseRate * 100).toFixed(1)}%` },
            { label: "Optimization", value: `${(optimizationFactor * 100).toFixed(0)}%` },
            { label: "Savings", value: savings },
            { label: "Optimized", value: optimizedHours }
          ],
          result: optimizedHours
        }
      }
    };
  }
}));
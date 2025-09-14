import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CalculatorSettings } from '../types/calculator.types';
import type { Document } from '../types/document.types';
import { useDocumentStore } from './documentStore';

// Preset configurations
export const CALCULATOR_PRESETS = {
  conservative: {
    name: 'Conservative',
    description: 'Higher time estimates, lower optimization',
    settings: {
      fieldTimeEstimates: {
        ifStatement: { current: 20 },
        precedentScript: { current: 45 },
        reflection: { current: 8 },
        search: { current: 15 },
        unbound: { current: 8 },
        builtInScript: { current: 25 },
        extended: { current: 15 },
        scripted: { current: 30 }
      },
      complexityMultipliers: {
        simple: { current: 1.2 },
        moderate: { current: 2.0 },
        complex: { current: 3.5 }
      },
      optimization: {
        reuseEfficiency: { current: 30 },
        learningCurve: { current: 5 },
        automationPotential: { current: 10 }
      }
    }
  },
  balanced: {
    name: 'Balanced',
    description: 'Default balanced estimates',
    settings: {
      fieldTimeEstimates: {
        ifStatement: { current: 15 },
        precedentScript: { current: 30 },
        reflection: { current: 5 },
        search: { current: 10 },
        unbound: { current: 5 },
        builtInScript: { current: 15 },
        extended: { current: 10 },
        scripted: { current: 20 }
      },
      complexityMultipliers: {
        simple: { current: 1.0 },
        moderate: { current: 1.5 },
        complex: { current: 2.5 }
      },
      optimization: {
        reuseEfficiency: { current: 40 },
        learningCurve: { current: 10 },
        automationPotential: { current: 20 }
      }
    }
  },
  aggressive: {
    name: 'Aggressive',
    description: 'Lower time estimates, higher optimization',
    settings: {
      fieldTimeEstimates: {
        ifStatement: { current: 10 },
        precedentScript: { current: 20 },
        reflection: { current: 3 },
        search: { current: 7 },
        unbound: { current: 3 },
        builtInScript: { current: 10 },
        extended: { current: 7 },
        scripted: { current: 15 }
      },
      complexityMultipliers: {
        simple: { current: 0.8 },
        moderate: { current: 1.2 },
        complex: { current: 2.0 }
      },
      optimization: {
        reuseEfficiency: { current: 60 },
        learningCurve: { current: 20 },
        automationPotential: { current: 35 }
      }
    }
  }
};

interface CalculatorStore {
  settings: CalculatorSettings;
  isOpen: boolean;
  originalSettings: CalculatorSettings | null;
  previewActive: boolean;
  isCalculating: boolean;
  calculationProgress: number;
  previewImpact: {
    totalDocuments: number;
    totalHoursBefore: number;
    totalHoursAfter: number;
    totalSavings: number;
    percentChange: number;
    complexityBreakdown?: {
      simple: { count: number; hours: number };
      moderate: { count: number; hours: number };
      complex: { count: number; hours: number };
    };
    confidenceLevel?: number;
  } | null;
  
  // Validation state
  validationErrors: string[];
  
  // History for undo/redo
  history: CalculatorSettings[];
  historyIndex: number;
  
  // Memoization cache
  calculationCache: Map<string, any>;
  
  // Actions
  openCalculator: () => void;
  closeCalculator: () => void;
  updateFieldTime: (field: keyof CalculatorSettings['fieldTimeEstimates'], value: number) => void;
  updateComplexityThreshold: (complexity: 'simple' | 'moderate', field: string, value: number) => void;
  updateComplexityMultiplier: (complexity: 'simple' | 'moderate' | 'complex', value: number) => void;
  updateOptimization: (field: keyof CalculatorSettings['optimization'], value: number) => void;
  resetToDefaults: () => void;
  applyPreset: (preset: keyof typeof CALCULATOR_PRESETS) => void;
  applySettings: () => void;
  calculatePreviewImpact: () => void;
  validateSettings: () => boolean;
  undo: () => void;
  redo: () => void;
  exportSettings: () => string;
  importSettings: (json: string) => boolean;
  
  // Calculations
  recalculateDocument: (document: Document, customSettings?: CalculatorSettings | null) => Document;
  recalculateDocumentOptimized: (document: Document, settings: CalculatorSettings) => Document;
}

const defaultSettings: CalculatorSettings = {
  baseTemplateTime: 0, // Start at 0 - all time should come from actual field calculations
  fieldTimeEstimates: {
    ifStatement: { min: 0, default: 15, max: 60, current: 15, unit: 'minutes' },
    precedentScript: { min: 0, default: 30, max: 120, current: 30, unit: 'minutes' },
    reflection: { min: 0, default: 5, max: 30, current: 5, unit: 'minutes' },
    search: { min: 0, default: 10, max: 45, current: 10, unit: 'minutes' },
    unbound: { min: 0, default: 5, max: 20, current: 5, unit: 'minutes' },
    builtInScript: { min: 0, default: 15, max: 60, current: 15, unit: 'minutes' },
    extended: { min: 0, default: 10, max: 40, current: 10, unit: 'minutes' },
    scripted: { min: 0, default: 20, max: 90, current: 20, unit: 'minutes' }
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
    simple: { min: 0, default: 1.0, max: 2.0, current: 1.0 },
    moderate: { min: 0, default: 1.5, max: 3.0, current: 1.5 },
    complex: { min: 0, default: 2.5, max: 5.0, current: 2.5 }
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

export const useCalculatorStore = create<CalculatorStore>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,
      isOpen: false,
      originalSettings: null,
      previewActive: false,
      isCalculating: false,
      calculationProgress: 0,
      previewImpact: null,
      validationErrors: [],
      history: [defaultSettings],
      historyIndex: 0,
      calculationCache: new Map(),
      
      openCalculator: () => set({ 
        isOpen: true, 
        originalSettings: get().settings,
        previewActive: true,
        validationErrors: []
      }),
      
      closeCalculator: () => set({ 
        isOpen: false, 
        originalSettings: null,
        previewActive: false,
        previewImpact: null,
        validationErrors: [],
        isCalculating: false,
        calculationProgress: 0
      }),
      
      updateFieldTime: (field, value) => {
        const { settings } = get();
        const newSettings = {
          ...settings,
          fieldTimeEstimates: {
            ...settings.fieldTimeEstimates,
            [field]: {
              ...settings.fieldTimeEstimates[field],
              current: value
            }
          }
        };
        
        // Add to history
        const { history, historyIndex } = get();
        const newHistory = [...history.slice(0, historyIndex + 1), newSettings];
        
        set({
          settings: newSettings,
          history: newHistory,
          historyIndex: newHistory.length - 1
        });
        
        // Validate and calculate preview
        get().validateSettings();
        get().calculatePreviewImpact();
      },
      
      updateComplexityThreshold: (complexity, field, value) => {
        const { settings } = get();
        const newSettings = {
          ...settings,
          complexityThresholds: {
            ...settings.complexityThresholds,
            [complexity]: {
              ...settings.complexityThresholds[complexity],
              [field]: value
            }
          }
        };
        
        set({ settings: newSettings });
        get().validateSettings();
        get().calculatePreviewImpact();
      },
      
      updateComplexityMultiplier: (complexity, value) => {
        const { settings } = get();
        const newSettings = {
          ...settings,
          complexityMultipliers: {
            ...settings.complexityMultipliers,
            [complexity]: {
              ...settings.complexityMultipliers[complexity],
              current: value
            }
          }
        };
        
        set({ settings: newSettings });
        get().validateSettings();
        get().calculatePreviewImpact();
      },
      
      updateOptimization: (field, value) => {
        const { settings } = get();
        const newSettings = {
          ...settings,
          optimization: {
            ...settings.optimization,
            [field]: {
              ...settings.optimization[field],
              current: value
            }
          }
        };
        
        set({ settings: newSettings });
        get().calculatePreviewImpact();
      },
      
      resetToDefaults: () => {
        set({ 
          settings: defaultSettings,
          validationErrors: [],
          history: [defaultSettings],
          historyIndex: 0
        });
        get().calculatePreviewImpact();
      },
      
      applyPreset: (preset) => {
        const presetConfig = CALCULATOR_PRESETS[preset];
        const { settings } = get();
        
        // Merge preset with current settings
        const newSettings = {
          ...settings,
          fieldTimeEstimates: Object.entries(settings.fieldTimeEstimates).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              ...value,
              current: presetConfig.settings.fieldTimeEstimates[key as keyof typeof presetConfig.settings.fieldTimeEstimates]?.current || value.current
            }
          }), {} as typeof settings.fieldTimeEstimates),
          complexityMultipliers: Object.entries(settings.complexityMultipliers).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              ...value,
              current: presetConfig.settings.complexityMultipliers[key as keyof typeof presetConfig.settings.complexityMultipliers]?.current || value.current
            }
          }), {} as typeof settings.complexityMultipliers),
          optimization: Object.entries(settings.optimization).reduce((acc, [key, value]) => ({
            ...acc,
            [key]: {
              ...value,
              current: presetConfig.settings.optimization[key as keyof typeof presetConfig.settings.optimization]?.current || value.current
            }
          }), {} as typeof settings.optimization)
        };
        
        set({ settings: newSettings, validationErrors: [] });
        get().calculatePreviewImpact();
      },
      
      validateSettings: () => {
        const { settings } = get();
        const errors: string[] = [];
        
        // Validate complexity thresholds don't overlap
        if (settings.complexityThresholds.simple.maxFields >= settings.complexityThresholds.moderate.minFields) {
          errors.push('Simple max fields must be less than moderate min fields');
        }
        
        if (settings.complexityThresholds.simple.maxIfStatements >= settings.complexityThresholds.moderate.maxIfStatements) {
          errors.push('Simple max IF statements should be less than moderate max');
        }
        
        // Validate multipliers are in ascending order
        if (settings.complexityMultipliers.simple.current >= settings.complexityMultipliers.moderate.current) {
          errors.push('Simple multiplier should be less than moderate');
        }
        
        if (settings.complexityMultipliers.moderate.current >= settings.complexityMultipliers.complex.current) {
          errors.push('Moderate multiplier should be less than complex');
        }
        
        // Validate optimization percentages
        const totalOptimization = 
          settings.optimization.reuseEfficiency.current +
          settings.optimization.learningCurve.current +
          settings.optimization.automationPotential.current;
        
        if (totalOptimization > 100) {
          errors.push('Total optimization cannot exceed 100%');
        }
        
        set({ validationErrors: errors });
        return errors.length === 0;
      },
      
      undo: () => {
        const { history, historyIndex } = get();
        if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          set({
            settings: history[newIndex],
            historyIndex: newIndex
          });
          get().calculatePreviewImpact();
        }
      },
      
      redo: () => {
        const { history, historyIndex } = get();
        if (historyIndex < history.length - 1) {
          const newIndex = historyIndex + 1;
          set({
            settings: history[newIndex],
            historyIndex: newIndex
          });
          get().calculatePreviewImpact();
        }
      },
      
      exportSettings: () => {
        const { settings } = get();
        return JSON.stringify(settings, null, 2);
      },
      
      importSettings: (json) => {
        try {
          const imported = JSON.parse(json);
          // Validate structure
          if (imported.fieldTimeEstimates && imported.complexityThresholds) {
            set({ settings: imported });
            get().validateSettings();
            get().calculatePreviewImpact();
            return true;
          }
          return false;
        } catch {
          return false;
        }
      },
      
      applySettings: () => {
        const { settings, validationErrors } = get();
        
        if (validationErrors.length > 0) {
          console.error('Cannot apply settings with validation errors:', validationErrors);
          return;
        }
        
        set({ 
          originalSettings: settings, 
          previewActive: false, 
          previewImpact: null,
          calculationCache: new Map() // Clear cache on apply
        });
        
        // Trigger live recalculation of all documents
        const documentStore = useDocumentStore.getState();
        documentStore.recalculateAllDocuments(settings);
      },
      
      calculatePreviewImpact: async () => {
        const { settings, originalSettings } = get();
        
        if (!originalSettings) {
          set({ previewImpact: null });
          return;
        }
        
        set({ isCalculating: true, calculationProgress: 0 });
        
        // Get documents from store
        const documentStore = useDocumentStore.getState();
        const documents = documentStore.documents;
        
        // Use sampling for large datasets (>100 documents)
        const sampleSize = documents.length > 100 ? 100 : documents.length;
        const sampledDocs = documents.length > 100 
          ? documents.sort(() => 0.5 - Math.random()).slice(0, sampleSize)
          : documents;
        
        let totalHoursBefore = 0;
        let totalHoursAfter = 0;
        const complexityBreakdown = {
          simple: { count: 0, hours: 0 },
          moderate: { count: 0, hours: 0 },
          complex: { count: 0, hours: 0 }
        };
        
        // Process in chunks to update progress
        const chunkSize = 20;
        for (let i = 0; i < sampledDocs.length; i += chunkSize) {
          const chunk = sampledDocs.slice(i, i + chunkSize);
          
          await new Promise(resolve => setTimeout(resolve, 0)); // Allow UI to update
          
          chunk.forEach(doc => {
            // Calculate with original settings
            const originalDoc = get().recalculateDocumentOptimized(doc, originalSettings);
            totalHoursBefore += originalDoc.effort?.optimized || 0;
            
            // Calculate with new settings  
            const newDoc = get().recalculateDocumentOptimized(doc, settings);
            totalHoursAfter += newDoc.effort?.optimized || 0;
            
            // Track complexity breakdown
            const complexity = ((newDoc.complexity as any)?.level || newDoc.complexity || 'simple').toLowerCase() as 'simple' | 'moderate' | 'complex';
            complexityBreakdown[complexity].count++;
            complexityBreakdown[complexity].hours += newDoc.effort?.optimized || 0;
          });
          
          set({ calculationProgress: Math.round((i + chunkSize) / sampledDocs.length * 100) });
        }
        
        // Extrapolate if sampling
        if (documents.length > sampleSize) {
          const factor = documents.length / sampleSize;
          totalHoursBefore *= factor;
          totalHoursAfter *= factor;
          Object.keys(complexityBreakdown).forEach(key => {
            const k = key as keyof typeof complexityBreakdown;
            complexityBreakdown[k].count = Math.round(complexityBreakdown[k].count * factor);
            complexityBreakdown[k].hours = Math.round(complexityBreakdown[k].hours * factor);
          });
        }
        
        const totalSavings = totalHoursBefore - totalHoursAfter;
        const percentChange = totalHoursBefore > 0 
          ? ((totalHoursAfter - totalHoursBefore) / totalHoursBefore) * 100 
          : 0;
        
        // Calculate confidence level based on sample size
        const confidenceLevel = documents.length > 100 
          ? Math.min(95, 80 + (sampleSize / documents.length) * 20)
          : 100;
        
        set({
          previewImpact: {
            totalDocuments: documents.length,
            totalHoursBefore: Math.round(totalHoursBefore),
            totalHoursAfter: Math.round(totalHoursAfter),
            totalSavings: Math.round(totalSavings),
            percentChange: Math.round(percentChange * 10) / 10,
            complexityBreakdown,
            confidenceLevel
          },
          isCalculating: false,
          calculationProgress: 100
        });
      },
      
      recalculateDocumentOptimized: (document, settings) => {
        // Create cache key
        const cacheKey = `${document.id}_${JSON.stringify(settings)}`;
        
        // Check cache
        const { calculationCache } = get();
        if (calculationCache.has(cacheKey)) {
          return calculationCache.get(cacheKey);
        }
        
        // Perform calculation
        const result = get().recalculateDocument(document, settings);
        
        // Store in cache (limit cache size)
        if (calculationCache.size > 1000) {
          const firstKey = calculationCache.keys().next().value!;
          calculationCache.delete(firstKey);
        }
        calculationCache.set(cacheKey, result);
        
        return result;
      },
      
      recalculateDocument: (document, customSettings = null) => {
        const settings = customSettings || get().settings;
        
        // Handle both database format (fieldTypes) and legacy format (fields)
        const getFieldCount = (fieldName: string): number => {
          // Database format: document.fieldTypes.ifStatement
          if (document.fieldTypes) {
            const mapping: Record<string, string> = {
              'if': 'ifStatement',
              'precedentScript': 'precedentScript',
              'reflection': 'reflection',
              'search': 'search',
              'unbound': 'unbound',
              'builtInScript': 'builtInScript',
              'extended': 'extended',
              'scripted': 'scripted'
            };
            return document.fieldTypes[mapping[fieldName] as keyof typeof document.fieldTypes] || 0;
          }
          // Legacy format: (document.fields || 0).if.count
          if ((document.fields || 0) && typeof (document.fields || 0) === 'object' && 'if' in (document.fields || 0)) {
            return ((document.fields || 0) as any)[fieldName]?.count || 0;
          }
          return 0;
        };
        
        // Start with base template time (converted to hours)
        // FIXED: Respect zero value - no default fallback
        const baseTemplateHours = (settings.baseTemplateTime || 0) / 60;
        
        // Calculate additional time based on field counts and current settings
        const precedentCount = getFieldCount('precedentScript');
        const precedentMinutes = settings.fieldTimeEstimates.precedentScript.current;
        
        // Debug logging for test doc
        if (document.name === 'test doc.docx') {
          console.log('=== Calculating test doc.docx ===');
          console.log('Precedent scripts:', precedentCount);
          console.log('Minutes per script:', precedentMinutes);
          console.log('Base template time:', settings.baseTemplateTime);
        }
        
        const fieldTime = 
          getFieldCount('if') * (settings.fieldTimeEstimates.ifStatement.current / 60) +
          precedentCount * (precedentMinutes / 60) +
          getFieldCount('reflection') * (settings.fieldTimeEstimates.reflection.current / 60) +
          getFieldCount('search') * (settings.fieldTimeEstimates.search.current / 60) +
          getFieldCount('unbound') * (settings.fieldTimeEstimates.unbound.current / 60) +
          getFieldCount('builtInScript') * (settings.fieldTimeEstimates.builtInScript.current / 60) +
          getFieldCount('extended') * (settings.fieldTimeEstimates.extended.current / 60) +
          getFieldCount('scripted') * (settings.fieldTimeEstimates.scripted.current / 60);
        
        // Total base effort is base template time plus field-specific time
        const totalBaseTime = baseTemplateHours + fieldTime;
        
        // Determine complexity
        const totalFields = document.totals?.allFields || 
                          (document.fieldTypes ? Object.values(document.fieldTypes).reduce((sum: number, val) => sum + (val as number), 0) : 0) ||
                          (typeof (document.fields || 0) === 'number' ? (document.fields || 0) : 0);
        const totalScripts = getFieldCount('precedentScript') + 
                            getFieldCount('builtInScript') + 
                            getFieldCount('scripted');
        const ifStatements = getFieldCount('if');
        
        let complexity: 'Simple' | 'Moderate' | 'Complex';
        let complexityReason: string;
        
        if (totalFields < settings.complexityThresholds.simple.maxFields &&
            totalScripts <= settings.complexityThresholds.simple.maxScripts &&
            ifStatements <= settings.complexityThresholds.simple.maxIfStatements) {
          complexity = 'Simple';
          complexityReason = `<${settings.complexityThresholds.simple.maxFields} fields, ≤${settings.complexityThresholds.simple.maxScripts} scripts`;
        } else if (totalFields >= settings.complexityThresholds.moderate.minFields &&
                   totalFields <= settings.complexityThresholds.moderate.maxFields &&
                   totalScripts < settings.complexityThresholds.moderate.maxScripts &&
                   ifStatements <= settings.complexityThresholds.moderate.maxIfStatements) {
          complexity = 'Moderate';
          complexityReason = `${settings.complexityThresholds.moderate.minFields}-${settings.complexityThresholds.moderate.maxFields} fields`;
        } else {
          complexity = 'Complex';
          complexityReason = `Exceeds moderate thresholds`;
        }
        
        // Apply complexity multiplier - ensure valid values
        const multiplier = settings.complexityMultipliers[complexity.toLowerCase() as 'simple' | 'moderate' | 'complex'].current || 1;
        const calculatedHours = (totalBaseTime || 0) * multiplier;
        
        // More debug for test doc
        if (document.name === 'test doc.docx') {
          console.log('Field time (hours):', fieldTime);
          console.log('Total base time:', totalBaseTime);
          console.log('Complexity:', complexity);
          console.log('Multiplier:', multiplier);
          console.log('Calculated hours:', calculatedHours);
        }
        
        // Calculate optimization with all three factors
        // Use actual reusability from document (calculated from field types) or 0
        const reuseRate = (document.reusability || 0) / 100;
        const reuseEfficiency = settings.optimization.reuseEfficiency.current / 100;
        const learningFactor = settings.optimization.learningCurve.current / 100;
        const automationFactor = settings.optimization.automationPotential.current / 100;
        
        // Apply optimization factors
        const reuseSavings = calculatedHours * reuseRate * reuseEfficiency;
        const learningSavings = calculatedHours * learningFactor * (1 - reuseRate); // Learning applies to non-reused parts
        const automationSavings = calculatedHours * automationFactor * 0.5; // Automation partially applies
        
        const totalSavings = Math.min(
          reuseSavings + learningSavings + automationSavings,
          calculatedHours * 0.8 // Cap savings at 80%
        );
        
        const optimizedHours = Math.max(calculatedHours - totalSavings, calculatedHours * 0.2); // Minimum 20% of original
        
        // Calculate totals for the document - ensure no NaN or undefined values
        const allFields = totalFields || 0;
        
        // Return updated document
        return {
          ...document,
          // Only use actual totals from SQL data - no fabrication
          totals: document.totals || {
            allFields
          },
          complexity: {
            level: complexity,
            reason: complexityReason,
            calculation: {
              formula: "(Base_Template_Time + Field_Time) × Complexity_Multiplier",
              inputs: {
                baseTemplateHours,
                fieldTime,
                totalBaseTime,
                multiplier
              },
              steps: [
                { label: "Base Template Time", value: `${baseTemplateHours.toFixed(2)}h` },
                { label: "Field Time", value: `${fieldTime.toFixed(2)}h` },
                { label: "Total Base Time", value: `${totalBaseTime.toFixed(2)}h` },
                { label: "Complexity", value: complexity },
                { label: "Multiplier", value: multiplier },
                { label: "Final Hours", value: `${calculatedHours.toFixed(2)}h` }
              ],
              result: calculatedHours
            }
          },
          effort: {
            calculated: calculatedHours,
            optimized: optimizedHours,
            savings: totalSavings,
            calculation: {
              formula: "Base - (Reuse + Learning + Automation)",
              inputs: {
                calculatedHours,
                reuseRate,
                reuseEfficiency,
                learningFactor,
                automationFactor
              },
              steps: [
                { label: "Base Hours", value: calculatedHours.toFixed(2) },
                { label: "Reuse Savings", value: reuseSavings.toFixed(1) },
                { label: "Learning Savings", value: learningSavings.toFixed(1) },
                { label: "Automation Savings", value: automationSavings.toFixed(1) },
                { label: "Total Savings", value: totalSavings.toFixed(1) },
                { label: "Optimized", value: optimizedHours.toFixed(2) }
              ],
              result: optimizedHours
            }
          }
        };
      }
    }),
    {
      name: 'calculator-settings',
      partialize: (state) => ({ 
        settings: state.settings,
        history: state.history.slice(-10) // Keep only last 10 for storage
      }),
      merge: (persisted: any, current) => {
        // Ensure all field estimates have min, max, default properties
        const mergedSettings = persisted?.settings || current.settings;
        
        // Deep merge fieldTimeEstimates to ensure all properties exist
        if (mergedSettings?.fieldTimeEstimates) {
          Object.keys(defaultSettings.fieldTimeEstimates).forEach(field => {
            const fieldKey = field as keyof typeof defaultSettings.fieldTimeEstimates;
            if (mergedSettings.fieldTimeEstimates[fieldKey]) {
              // Ensure min, max, default exist even if only current was saved
              mergedSettings.fieldTimeEstimates[fieldKey] = {
                ...defaultSettings.fieldTimeEstimates[fieldKey],
                ...mergedSettings.fieldTimeEstimates[fieldKey],
                min: mergedSettings.fieldTimeEstimates[fieldKey].min ?? defaultSettings.fieldTimeEstimates[fieldKey].min,
                max: mergedSettings.fieldTimeEstimates[fieldKey].max ?? defaultSettings.fieldTimeEstimates[fieldKey].max,
                default: mergedSettings.fieldTimeEstimates[fieldKey].default ?? defaultSettings.fieldTimeEstimates[fieldKey].default,
                // Ensure current is valid, use default if not set
                current: mergedSettings.fieldTimeEstimates[fieldKey].current ?? defaultSettings.fieldTimeEstimates[fieldKey].current
              };
            }
          });
        }
        
        return {
          ...current,
          ...persisted,
          settings: mergedSettings,
          calculationCache: new Map() // Always start with fresh cache
        };
      }
    }
  )
);
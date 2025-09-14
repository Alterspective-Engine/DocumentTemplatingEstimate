/**
 * Data Verification Utility
 * Ensures data consistency and accuracy across all components
 */

import { useDocumentStore } from '../store/documentStore';
import { useCalculatorStore } from '../store/calculatorStore';

// Type definitions for verification results
type CalculationVerificationResult = {
  valid: boolean;
  errors: string[];
  warnings: string[];
};

type StatisticsVerificationResult = {
  valid: boolean;
  errors: string[];
};

type FieldCountsVerificationResult = {
  valid: boolean;
  errors: string[];
};

export class DataVerificationService {
  private static instance: DataVerificationService;
  
  private constructor() {}
  
  static getInstance(): DataVerificationService {
    if (!DataVerificationService.instance) {
      DataVerificationService.instance = new DataVerificationService();
    }
    return DataVerificationService.instance;
  }

  /**
   * Verify that all documents have been calculated with current settings
   */
  verifyDocumentCalculations(): CalculationVerificationResult {
    const documentStore = useDocumentStore.getState();
    const calculatorStore = useCalculatorStore.getState();
    const { documents } = documentStore;
    const { settings } = calculatorStore;
    
    const errors: string[] = [];
    const warnings: string[] = [];
    
    documents.forEach(doc => {
      // Recalculate to verify
      const recalculated = calculatorStore.recalculateDocument(doc, settings);
      
      // Check if values match
      if (doc.effort?.calculated != null && recalculated.effort?.calculated != null && 
          Math.abs(doc.effort.calculated - recalculated.effort.calculated) > 0.01) {
        errors.push(`Document ${doc.name}: Calculated effort mismatch (${doc.effort.calculated} vs ${recalculated.effort.calculated})`);
      }
      
      if (doc.effort?.optimized != null && recalculated.effort?.optimized != null && 
          Math.abs(doc.effort.optimized - recalculated.effort.optimized) > 0.01) {
        errors.push(`Document ${doc.name}: Optimized effort mismatch (${doc.effort.optimized} vs ${recalculated.effort.optimized})`);
      }
      
      const docComplexity = (doc.complexity as any)?.level || doc.complexity;
      const recalcComplexity = (recalculated.complexity as any)?.level || recalculated.complexity;
      if (docComplexity !== recalcComplexity) {
        errors.push(`Document ${doc.name}: Complexity mismatch (${docComplexity} vs ${recalcComplexity})`);
      }
      
      // Check for invalid values
      const calculatedEffort = doc.effort?.calculated;
      const optimizedEffort = doc.effort?.optimized;
      const savings = doc.effort?.savings;
      
      if (calculatedEffort != null && (isNaN(calculatedEffort) || !isFinite(calculatedEffort))) {
        errors.push(`Document ${doc.name}: Invalid calculated effort value`);
      }
      
      if (optimizedEffort != null && (isNaN(optimizedEffort) || !isFinite(optimizedEffort))) {
        errors.push(`Document ${doc.name}: Invalid optimized effort value`);
      }
      
      // Warnings for potential issues
      if (optimizedEffort != null && calculatedEffort != null && optimizedEffort > calculatedEffort) {
        warnings.push(`Document ${doc.name}: Optimized effort exceeds calculated effort`);
      }
      
      if (savings != null && savings < 0) {
        warnings.push(`Document ${doc.name}: Negative savings detected`);
      }
    });
    
    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Verify statistics calculations
   */
  verifyStatistics(): StatisticsVerificationResult {
    const documentStore = useDocumentStore.getState();
    const { documents, getStatistics } = documentStore;
    const stats = getStatistics();
    
    const errors: string[] = [];
    
    // Manually calculate totals
    const manualTotalEffort = documents.reduce((sum, doc) => sum + (doc.effort?.calculated || 0), 0);
    const manualTotalOptimized = documents.reduce((sum, doc) => sum + (doc.effort?.optimized || 0), 0);
    const manualComplexityCount = {
      Simple: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Simple';
      }).length,
      Moderate: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Moderate';
      }).length,
      Complex: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Complex';
      }).length
    };
    
    // Verify totals match
    if (Math.abs(stats.totalEffort - manualTotalEffort) > 0.01) {
      errors.push(`Total effort mismatch: ${stats.totalEffort} vs ${manualTotalEffort}`);
    }
    
    if (Math.abs(stats.totalOptimizedEffort - manualTotalOptimized) > 0.01) {
      errors.push(`Total optimized effort mismatch: ${stats.totalOptimizedEffort} vs ${manualTotalOptimized}`);
    }
    
    // Verify complexity counts
    Object.entries(manualComplexityCount).forEach(([level, count]) => {
      if (stats.byComplexity[level] !== count) {
        errors.push(`Complexity count mismatch for ${level}: ${stats.byComplexity[level]} vs ${count}`);
      }
    });
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Verify field counts and totals
   */
  verifyFieldCounts(): FieldCountsVerificationResult {
    const documentStore = useDocumentStore.getState();
    const { documents } = documentStore;
    
    const errors: string[] = [];
    
    documents.forEach(doc => {
      // Calculate total fields from individual counts
      let calculatedTotal = 0;
      
      // Handle both database format (fieldTypes) and legacy format (fields)
      if (doc.fieldTypes) {
        // Database format
        calculatedTotal = 
          (doc.fieldTypes.ifStatement || 0) +
          (doc.fieldTypes.precedentScript || 0) +
          (doc.fieldTypes.reflection || 0) +
          (doc.fieldTypes.search || 0) +
          (doc.fieldTypes.unbound || 0) +
          (doc.fieldTypes.builtInScript || 0) +
          (doc.fieldTypes.extended || 0) +
          (doc.fieldTypes.scripted || 0);
      } else if (doc.fields && typeof doc.fields === 'object' && 'if' in doc.fields) {
        // Legacy format
        const fields = doc.fields as any;
        calculatedTotal = 
          (fields.if?.count || 0) +
          (fields.precedentScript?.count || 0) +
          (fields.reflection?.count || 0) +
          (fields.search?.count || 0) +
          (fields.unbound?.count || 0) +
          (fields.builtInScript?.count || 0) +
          (fields.extended?.count || 0) +
          (fields.scripted?.count || 0);
      } else if (typeof doc.fields === 'number') {
        // Simple number format
        calculatedTotal = doc.fields;
      }
      
      // Only check if totals exist
      if (doc.totals?.allFields && Math.abs(doc.totals.allFields - calculatedTotal) > 1) {
        errors.push(`Document ${doc.name}: Field total mismatch (${doc.totals.allFields} vs ${calculatedTotal})`);
      }
    });
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Comprehensive data integrity check
   */
  performFullVerification(): {
    summary: {
      totalChecks: number;
      passed: number;
      failed: number;
      warnings: number;
    };
    details: {
      calculations: CalculationVerificationResult;
      statistics: StatisticsVerificationResult;
      fieldCounts: FieldCountsVerificationResult;
    };
  } {
    const calculations = this.verifyDocumentCalculations();
    const statistics = this.verifyStatistics();
    const fieldCounts = this.verifyFieldCounts();
    
    const totalChecks = 3;
    const passed = [calculations, statistics, fieldCounts].filter(r => r.valid).length;
    
    return {
      summary: {
        totalChecks,
        passed,
        failed: totalChecks - passed,
        warnings: calculations.warnings.length
      },
      details: {
        calculations,
        statistics,
        fieldCounts
      }
    };
  }

  /**
   * Fix data inconsistencies by recalculating all documents
   */
  fixDataInconsistencies(): void {
    const documentStore = useDocumentStore.getState();
    const calculatorStore = useCalculatorStore.getState();
    
    // Force recalculation with current settings
    documentStore.recalculateAllDocuments(calculatorStore.settings);
    
    console.log('Data inconsistencies fixed - all documents recalculated');
  }
}

// Export singleton instance
export const dataVerification = DataVerificationService.getInstance();
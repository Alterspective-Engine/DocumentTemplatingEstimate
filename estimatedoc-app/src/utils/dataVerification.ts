/**
 * Data Verification Utility
 * Ensures data consistency and accuracy across all components
 */

import { useDocumentStore } from '../store/documentStore';
import { useCalculatorStore } from '../store/calculatorStore';
import type { Document } from '../types/document.types';

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
  verifyDocumentCalculations(): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
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
      if (Math.abs(doc.effort.calculated - recalculated.effort.calculated) > 0.01) {
        errors.push(`Document ${doc.name}: Calculated effort mismatch (${doc.effort.calculated} vs ${recalculated.effort.calculated})`);
      }
      
      if (Math.abs(doc.effort.optimized - recalculated.effort.optimized) > 0.01) {
        errors.push(`Document ${doc.name}: Optimized effort mismatch (${doc.effort.optimized} vs ${recalculated.effort.optimized})`);
      }
      
      if (doc.complexity.level !== recalculated.complexity.level) {
        errors.push(`Document ${doc.name}: Complexity mismatch (${doc.complexity.level} vs ${recalculated.complexity.level})`);
      }
      
      // Check for invalid values
      if (isNaN(doc.effort.calculated) || !isFinite(doc.effort.calculated)) {
        errors.push(`Document ${doc.name}: Invalid calculated effort value`);
      }
      
      if (isNaN(doc.effort.optimized) || !isFinite(doc.effort.optimized)) {
        errors.push(`Document ${doc.name}: Invalid optimized effort value`);
      }
      
      // Warnings for potential issues
      if (doc.effort.optimized > doc.effort.calculated) {
        warnings.push(`Document ${doc.name}: Optimized effort exceeds calculated effort`);
      }
      
      if (doc.effort.savings < 0) {
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
  verifyStatistics(): {
    valid: boolean;
    errors: string[];
  } {
    const documentStore = useDocumentStore.getState();
    const { documents, getStatistics } = documentStore;
    const stats = getStatistics();
    
    const errors: string[] = [];
    
    // Manually calculate totals
    const manualTotalEffort = documents.reduce((sum, doc) => sum + doc.effort.calculated, 0);
    const manualTotalOptimized = documents.reduce((sum, doc) => sum + doc.effort.optimized, 0);
    const manualComplexityCount = {
      Simple: documents.filter(d => d.complexity.level === 'Simple').length,
      Moderate: documents.filter(d => d.complexity.level === 'Moderate').length,
      Complex: documents.filter(d => d.complexity.level === 'Complex').length
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
  verifyFieldCounts(): {
    valid: boolean;
    errors: string[];
  } {
    const documentStore = useDocumentStore.getState();
    const { documents } = documentStore;
    
    const errors: string[] = [];
    
    documents.forEach(doc => {
      // Calculate total fields from individual counts
      const calculatedTotal = 
        doc.fields.if.count +
        doc.fields.precedentScript.count +
        doc.fields.reflection.count +
        doc.fields.search.count +
        doc.fields.unbound.count +
        doc.fields.builtInScript.count +
        doc.fields.extended.count +
        doc.fields.scripted.count;
      
      if (doc.totals.allFields !== calculatedTotal) {
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
      calculations: ReturnType<typeof this.verifyDocumentCalculations>;
      statistics: ReturnType<typeof this.verifyStatistics>;
      fieldCounts: ReturnType<typeof this.verifyFieldCounts>;
    };
  } {
    const calculations = this.verifyDocumentCalculations();
    const statistics = this.verifyStatistics();
    const fieldCounts = this.verifyFieldCounts();
    
    const totalErrors = 
      calculations.errors.length + 
      statistics.errors.length + 
      fieldCounts.errors.length;
    
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
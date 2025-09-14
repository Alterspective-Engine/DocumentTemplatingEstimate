export type Complexity = 'simple' | 'moderate' | 'complex';

export interface DocumentFields {
  ifStatement?: number;
  precedentScript?: number;
  reflection?: number;
  search?: number;
  unbound?: number;
  builtInScript?: number;
  extended?: number;
  scripted?: number;
}

export interface ComplexityObject {
  level: 'Simple' | 'Moderate' | 'Complex';
  factors?: {
    fields: number;
    scripts: number;
    conditionals: number;
  };
  reason?: string;
  calculation?: CalculationTrace;
}

export interface CalculationTrace {
  base: number;
  multiplier: number;
  total: number;
  breakdown: Record<string, number>;
}

export interface DocumentTotals {
  allFields: number;
  simple?: number;
  complex?: number;
  uniqueFields?: number;
  reusableFields?: number;
  reuseRate: string | number;
}

export interface DocumentEffort {
  calculated: number;
  optimized: number;
  savings: number;
  base?: number;
}

export interface Document {
  id: string;
  name: string;
  category?: string;
  description?: string;
  fields?: number | DocumentFields;
  fieldTypes?: DocumentFields;
  complexity?: Complexity | ComplexityObject;
  totals?: DocumentTotals;
  effort?: DocumentEffort;
  estimatedHours?: number;
  priority?: 'low' | 'medium' | 'high';
  tags?: string[];
  reuseRate?: number;
  reusability?: number;
  automationPotential?: number;
  implementationRisk?: 'low' | 'medium' | 'high';
  dependencies?: string[];
  notes?: string;
  lastUpdated?: string;
  status?: 'pending' | 'in-progress' | 'completed';
}

export interface CalculatorSettings {
  baseTemplateTime: number;
  fieldTimeEstimates: {
    ifStatement: { min: number; max: number; current: number };
    precedentScript: { min: number; max: number; current: number };
    reflection: { min: number; max: number; current: number };
    search: { min: number; max: number; current: number };
    unbound: { min: number; max: number; current: number };
    builtInScript: { min: number; max: number; current: number };
    extended: { min: number; max: number; current: number };
    scripted: { min: number; max: number; current: number };
  };
  complexityMultipliers: {
    simple: { value: number; current: number };
    moderate: { value: number; current: number };
    complex: { value: number; current: number };
  };
  optimization: {
    reuseEfficiency: { min: number; max: number; current: number };
    learningCurve: { min: number; max: number; current: number };
    automationPotential: { min: number; max: number; current: number };
  };
}

export interface DataSourceConfig {
  type: 'database' | 'hardcoded' | 'auto';
  useDatabaseIfAvailable: boolean;
  extractedDataPath?: string;
}

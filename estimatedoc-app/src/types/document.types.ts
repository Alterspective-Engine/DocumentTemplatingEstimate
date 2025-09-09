export interface FieldMetrics {
  count: number;
  unique: number;
  reusable: number;
  reuseRate: string;
  evidence: EvidenceLink;
}

export interface EvidenceLink {
  source: string;
  query?: string;
  calculation?: string;
  traceId: string;
}

export interface CalculationStep {
  label: string;
  value: number | string;
  formula?: string;
}

export interface CalculationTrace {
  formula: string;
  inputs: Record<string, number>;
  steps: CalculationStep[];
  result: number;
}

export interface DocumentFields {
  if: FieldMetrics;
  precedentScript: FieldMetrics;
  reflection: FieldMetrics;
  search: FieldMetrics;
  unbound: FieldMetrics;
  builtInScript: FieldMetrics;
  extended: FieldMetrics;
  scripted: FieldMetrics;
}

export interface DocumentTotals {
  allFields: number;
  uniqueFields: number;
  reusableFields: number;
  reuseRate: string;
}

export interface DocumentComplexity {
  level: 'Simple' | 'Moderate' | 'Complex';
  reason: string;
  calculation: CalculationTrace;
}

export interface DocumentEffort {
  calculated: number;
  optimized: number;
  savings: number;
  calculation: CalculationTrace;
}

export interface DocumentEvidence {
  source: 'SQL' | 'Estimated';
  files: string[];
  lastUpdated: Date;
}

export interface Document {
  id: number;
  name: string;
  description: string;
  sqlFilename: string;
  
  fields: DocumentFields;
  totals: DocumentTotals;
  complexity: DocumentComplexity;
  effort: DocumentEffort;
  evidence: DocumentEvidence;
  
  // Metadata
  sections?: number;
  tables?: number;
  checkboxes?: number;
}
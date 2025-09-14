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
  source: string; // Allow any string for source mapping strategies
  details?: string;
  query?: string;
  confidence?: number;
  files?: string[];
  lastUpdated?: Date;
  traceability?: {
    dataSource: string;
    analysisDate: string;
    documentId: number;
    mappingMethod: string;
  };
}

export interface Document {
  id: string | number;
  name: string;
  description: string;
  template?: string;
  fields?: number | DocumentFields;
  
  // Field types breakdown
  fieldTypes?: {
    ifStatement: number;
    precedentScript: number;
    reflection: number;
    search: number;
    unbound: number;
    builtInScript: number;
    extended: number;
    scripted: number;
  };
  
  // Complexity assessment
  complexity: {
    level: 'Simple' | 'Moderate' | 'Complex';
    factors?: {
      fields: number;
      scripts: number;
      conditionals: number;
    };
    reason?: string;
    calculation?: CalculationTrace;
  };
  
  // Effort calculation
  effort: {
    base?: number;
    calculated?: number;
    optimized?: number;
    savings?: number;
    calculation?: CalculationTrace;
  };
  
  // Evidence tracking
  evidence: {
    source: 'SQL' | 'Estimated' | string;
    confidence?: number;
    lastUpdated?: string | Date;
    details?: string;
    query?: string;
    files?: string[];
    traceability?: {
      dataSource: string;
      analysisDate: string;
      documentId: number;
      mappingMethod: string;
    };
  };
  
  // Reusability and risk
  reusability?: number;
  risk?: 'low' | 'medium' | 'high';
  status?: 'pending' | 'processing' | 'completed';
  
  // Additional properties used by DocumentCard
  estimatedHours?: number;
  reuseRate?: number;
  automationPotential?: number;
  implementationRisk?: 'low' | 'medium' | 'high';
  tags?: string[];
  category?: string;
  
  // Extended metadata
  metadata?: {
    sqlDocId?: number;
    sqlFilename?: string;
    manifestCode?: string;
    clientComplexity?: string;
    createdAt?: string;
  };
  
  // Legacy fields for compatibility
  sqlFilename?: string;
  totals?: DocumentTotals;
  sections?: number;
  tables?: number;
  checkboxes?: number;
}
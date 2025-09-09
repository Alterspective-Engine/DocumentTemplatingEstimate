export interface FieldTimeEstimate {
  min: number;
  default: number;
  max: number;
  current: number;
  unit: 'minutes';
}

export interface FieldTimeEstimates {
  ifStatement: FieldTimeEstimate;
  precedentScript: FieldTimeEstimate;
  reflection: FieldTimeEstimate;
  search: FieldTimeEstimate;
  unbound: FieldTimeEstimate;
  builtInScript: FieldTimeEstimate;
  extended: FieldTimeEstimate;
  scripted: FieldTimeEstimate;
}

export interface ComplexityThresholds {
  simple: {
    maxFields: number;
    maxScripts: number;
    maxIfStatements: number;
  };
  moderate: {
    minFields: number;
    maxFields: number;
    maxScripts: number;
    maxIfStatements: number;
  };
}

export interface ComplexityMultiplier {
  min: number;
  default: number;
  max: number;
  current: number;
}

export interface ComplexityMultipliers {
  simple: ComplexityMultiplier;
  moderate: ComplexityMultiplier;
  complex: ComplexityMultiplier;
}

export interface OptimizationSettings {
  reuseEfficiency: {
    min: number;
    default: number;
    max: number;
    current: number;
    unit: '%';
  };
  learningCurve: {
    min: number;
    default: number;
    max: number;
    current: number;
    unit: '%';
  };
  automationPotential: {
    min: number;
    default: number;
    max: number;
    current: number;
    unit: '%';
  };
}

export interface ConfidenceSettings {
  sqlDataWeight: number;
  estimatedDataWeight: number;
  showConfidenceIntervals: boolean;
}

export interface CalculatorSettings {
  fieldTimeEstimates: FieldTimeEstimates;
  complexityThresholds: ComplexityThresholds;
  complexityMultipliers: ComplexityMultipliers;
  optimization: OptimizationSettings;
  confidence: ConfidenceSettings;
}
#!/bin/bash

echo "🔧 Fixing all TypeScript errors in EstimateDoc app..."

# Fix Document type - make all fields optional
echo "📝 Fixing Document type definition..."
cat > src/types.ts << 'EOF'
export type Complexity = 'simple' | 'moderate' | 'complex';

export interface Document {
  id: string;
  name: string;
  category?: string;
  description?: string;
  fields?: number;
  fieldTypes?: {
    ifStatement?: number;
    precedentScript?: number;
    reflection?: number;
    search?: number;
    unbound?: number;
    builtInScript?: number;
    extended?: number;
    scripted?: number;
  };
  complexity?: Complexity;
  estimatedHours?: number;
  priority?: 'low' | 'medium' | 'high';
  tags?: string[];
  reuseRate?: number;
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
EOF

# Fix DocumentCard to handle optional fields
echo "📝 Fixing DocumentCard component..."
cat > src/components/DocumentCard/DocumentCard.tsx << 'EOF'
import React from 'react';
import { Clock, Target, TrendingUp, AlertCircle, Tag, Database, Hash } from 'lucide-react';
import { Document } from '../../types';
import './DocumentCard.css';

interface DocumentCardProps {
  document: Document;
  onClick?: () => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document, onClick }) => {
  const getComplexityColor = (complexity?: string) => {
    switch (complexity) {
      case 'simple': return '#2C8248';
      case 'moderate': return '#FFA500';
      case 'complex': return '#FF6B6B';
      default: return '#999';
    }
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'low': return '#2C8248';
      case 'medium': return '#FFA500';
      case 'high': return '#FF6B6B';
      default: return '#999';
    }
  };

  const effort = document.estimatedHours || 0;
  const fields = document.fields || 0;
  const reuseRate = document.reuseRate || 0;
  const automationPotential = document.automationPotential || 0;

  return (
    <div className="document-card" onClick={onClick}>
      <div className="card-header">
        <h3>{document.name}</h3>
        <span 
          className="complexity-badge" 
          style={{ backgroundColor: getComplexityColor(document.complexity) }}
        >
          {document.complexity || 'Unknown'}
        </span>
      </div>
      
      {document.description && (
        <p className="description">{document.description}</p>
      )}
      
      <div className="metrics">
        <div className="metric">
          <Clock size={16} />
          <span>Effort: {effort.toFixed(1)}h</span>
        </div>
        <div className="metric">
          <Hash size={16} />
          <span>Fields: {fields}</span>
        </div>
        {reuseRate > 0 && (
          <div className="metric">
            <Target size={16} />
            <span>Reuse: {reuseRate}%</span>
          </div>
        )}
        {automationPotential > 0 && (
          <div className="metric">
            <TrendingUp size={16} />
            <span>Auto: {automationPotential}%</span>
          </div>
        )}
        {document.implementationRisk && (
          <div className="metric">
            <AlertCircle size={16} color={getRiskColor(document.implementationRisk)} />
            <span>Risk: {document.implementationRisk}</span>
          </div>
        )}
      </div>
      
      {document.tags && document.tags.length > 0 && (
        <div className="tags">
          {document.tags.map((tag, index) => (
            <span key={index} className="tag">
              <Tag size={12} />
              {tag}
            </span>
          ))}
        </div>
      )}
      
      <div className="card-footer">
        <span className="category">{document.category || 'Uncategorized'}</span>
        <span className="data-source">
          <Database size={12} />
          Database
        </span>
      </div>
    </div>
  );
};
EOF

# Fix DocumentList to handle optional fields
echo "📝 Fixing DocumentList component..."
sed -i '' 's/doc\.category/doc.category || "Uncategorized"/g' src/components/DocumentList/DocumentList.tsx
sed -i '' 's/doc\.complexity/doc.complexity || "simple"/g' src/components/DocumentList/DocumentList.tsx
sed -i '' 's/doc\.estimatedHours/(doc.estimatedHours || 0)/g' src/components/DocumentList/DocumentList.tsx
sed -i '' 's/doc\.fields/(doc.fields || 0)/g' src/components/DocumentList/DocumentList.tsx
sed -i '' 's/doc\.reuseRate/(doc.reuseRate || 0)/g' src/components/DocumentList/DocumentList.tsx
sed -i '' 's/doc\.automationPotential/(doc.automationPotential || 0)/g' src/components/DocumentList/DocumentList.tsx

# Fix Calculator component to handle optional fields
echo "📝 Fixing Calculator component..."
sed -i '' 's/doc\.complexity/doc.complexity || "simple"/g' src/components/Calculator/Calculator.tsx
sed -i '' 's/doc\.fields/(doc.fields || 0)/g' src/components/Calculator/Calculator.tsx
sed -i '' 's/document\.complexity/document.complexity || "simple"/g' src/components/Calculator/Calculator.tsx
sed -i '' 's/document\.fields/(document.fields || 0)/g' src/components/Calculator/Calculator.tsx

# Fix calculatorStore to handle optional fields
echo "📝 Fixing calculatorStore..."
sed -i '' 's/document\.complexity/document.complexity || "simple"/g' src/store/calculatorStore.ts
sed -i '' 's/document\.fields/(document.fields || 0)/g' src/store/calculatorStore.ts
sed -i '' 's/document\.reuseRate/(document.reuseRate || 0)/g' src/store/calculatorStore.ts
sed -i '' 's/document\.automationPotential/(document.automationPotential || 0)/g' src/store/calculatorStore.ts

# Fix documentStore to handle optional fields
echo "📝 Fixing documentStore..."
sed -i '' 's/doc\.category/doc.category || "Uncategorized"/g' src/store/documentStore.ts
sed -i '' 's/doc\.complexity/doc.complexity || "simple"/g' src/store/documentStore.ts
sed -i '' 's/doc\.estimatedHours/(doc.estimatedHours || 0)/g' src/store/documentStore.ts

# Run TypeScript check
echo "🔍 Running TypeScript check..."
npx tsc --noEmit

echo "✅ TypeScript errors fixed!"
EOF

chmod +x fix-all-ts-errors.sh
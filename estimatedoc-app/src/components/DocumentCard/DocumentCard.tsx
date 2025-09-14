import React from 'react';
import { Clock, Target, TrendingUp, AlertCircle, Tag, Database, Hash } from 'lucide-react';
import type { Document } from '../../types/document.types';
import './DocumentCard.css';

interface DocumentCardProps {
  document: Document;
  onClick?: () => void;
  selected?: boolean;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document, onClick, selected }) => {
  const getComplexityColor = (complexity?: string | object) => {
    const complexityStr = typeof complexity === 'object' && complexity !== null 
      ? (complexity as any).level || 'simple'
      : (complexity as string) || 'simple';
    switch (complexityStr.toLowerCase()) {
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

  const effort = document.effort?.calculated || 0;
  const fields = document.totals?.allFields || document.fields || 0;
  const reusability = document.reusability || 0;
  const automationPotential = document.automationPotential || 0;

  return (
    <div className={`document-card ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="card-header">
        <h3>{document.name}</h3>
        <span 
          className="complexity-badge" 
          style={{ backgroundColor: getComplexityColor(document.complexity) }}
        >
          {typeof document.complexity === 'object' && document.complexity !== null 
            ? (document.complexity as any).level || 'Unknown'
            : document.complexity || 'Unknown'}
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
        {reusability > 0 && (
          <div className="metric">
            <Target size={16} />
            <span>Reuse: {reusability}%</span>
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
        <span className={`data-source ${document.evidence?.source?.toLowerCase()}`}>
          <Database size={12} />
          {document.evidence?.source || 'Unknown'}
        </span>
      </div>
    </div>
  );
};

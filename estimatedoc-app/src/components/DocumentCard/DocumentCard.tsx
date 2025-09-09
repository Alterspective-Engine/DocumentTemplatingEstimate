import React from 'react';
import type { Document } from '../../types/document.types';
import { FileText, Clock, Layers, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';
import './DocumentCard.css';

interface DocumentCardProps {
  document: Document;
  onClick: (document: Document) => void;
  selected?: boolean;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ 
  document, 
  onClick, 
  selected = false 
}) => {
  const getComplexityColor = (level: string) => {
    switch (level) {
      case 'Simple': return 'success';
      case 'Moderate': return 'warning';
      case 'Complex': return 'error';
      default: return 'primary';
    }
  };

  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    return `${hours.toFixed(1)}h`;
  };

  return (
    <div 
      className={`document-card ${selected ? 'selected' : ''}`}
      onClick={() => onClick(document)}
    >
      <div className="card-header">
        <div className="card-title-group">
          <FileText size={20} className="card-icon" />
          <h3 className="title-medium">{document.name}</h3>
        </div>
        <span className={`complexity-badge badge-${getComplexityColor(document.complexity.level)}`}>
          {document.complexity.level}
        </span>
      </div>
      
      <p className="card-description body-medium">
        {document.description}
      </p>
      
      <div className="card-metrics">
        <div className="metric">
          <Layers size={16} className="metric-icon" />
          <div className="metric-content">
            <span className="label-small">Fields</span>
            <span className="body-large">{document.totals.allFields}</span>
          </div>
        </div>
        
        <div className="metric">
          <Clock size={16} className="metric-icon" />
          <div className="metric-content">
            <span className="label-small">Effort</span>
            <span className="body-large">{formatHours(document.effort.calculated)}</span>
          </div>
        </div>
        
        <div className="metric">
          <TrendingUp size={16} className="metric-icon" />
          <div className="metric-content">
            <span className="label-small">Reuse</span>
            <span className="body-large">{document.totals.reuseRate}</span>
          </div>
        </div>
      </div>
      
      <div className="card-footer">
        <div className="evidence-indicator">
          {document.evidence.source === 'SQL' ? (
            <div className="evidence-badge evidence-sql">
              <CheckCircle size={14} />
              <span className="label-small">SQL Data</span>
            </div>
          ) : (
            <div className="evidence-badge evidence-estimated">
              <AlertCircle size={14} />
              <span className="label-small">Estimated</span>
            </div>
          )}
        </div>
        
        {document.effort.savings > 0 && (
          <div className="savings-indicator">
            <span className="label-small">Save {formatHours(document.effort.savings)}</span>
          </div>
        )}
      </div>
    </div>
  );
};
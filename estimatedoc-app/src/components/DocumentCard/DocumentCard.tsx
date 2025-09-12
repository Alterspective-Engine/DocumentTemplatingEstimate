import React, { useEffect, useState } from 'react';
import type { Document } from '../../types/document.types';
import { FileText, Clock, Layers, TrendingUp, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { useDocumentStore } from '../../store/documentStore';
import { useHistoryStore } from '../../store/historyStore';
import { MiniGraph } from '../MiniGraph/MiniGraph';
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
  const { updatingDocuments } = useDocumentStore();
  const { getDocumentHistory } = useHistoryStore();
  const [isUpdating, setIsUpdating] = useState(false);
  const [showChange, setShowChange] = useState(false);
  
  const history = getDocumentHistory(document.id.toString());
  const effortHistory = history?.effort.map(h => h.value) || [];
  const optimizedHistory = history?.optimized.map(h => h.value) || [];
  const fieldsHistory = history?.fields.map(h => h.value) || [];
  
  // Check if this document is updating
  useEffect(() => {
    const updating = updatingDocuments.has(document.id.toString());
    setIsUpdating(updating);
    
    if (updating) {
      setShowChange(true);
      const timer = setTimeout(() => setShowChange(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [updatingDocuments, document.id]);
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
      className={`document-card ${selected ? 'selected' : ''} ${isUpdating ? 'updating' : ''}`}
      onClick={() => onClick(document)}
    >
      {isUpdating && (
        <div className="update-indicator">
          <RefreshCw size={14} className="spin" />
          <span>Updating...</span>
        </div>
      )}
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
        <div className={`metric ${showChange ? 'value-changed' : ''}`}>
          <Layers size={16} className="metric-icon" />
          <div className="metric-content">
            <span className="label-small">Fields</span>
            <div className="metric-value-with-graph">
              <span className="body-large">{document.totals.allFields}</span>
              {fieldsHistory.length > 1 && (
                <MiniGraph 
                  data={fieldsHistory} 
                  width={40} 
                  height={16}
                  color="#B8B8B8"
                  showTrend={false}
                />
              )}
            </div>
          </div>
        </div>
        
        <div className={`metric ${showChange ? 'value-changed' : ''}`}>
          <Clock size={16} className="metric-icon" />
          <div className="metric-content">
            <span className="label-small">Effort</span>
            <div className="metric-value-with-graph">
              <span className="body-large">{formatHours(document.effort.calculated)}</span>
              {effortHistory.length > 1 && (
                <MiniGraph 
                  data={effortHistory} 
                  width={40} 
                  height={16}
                  color="#FFD93D"
                  showTrend={false}
                />
              )}
            </div>
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
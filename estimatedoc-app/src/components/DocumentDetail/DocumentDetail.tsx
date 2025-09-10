import React, { useState } from 'react';
import type { Document } from '../../types/document.types';
import { 
  X, FileText, Clock, TrendingUp, Info, 
  Database, Layers,
  Code, Search, Link, Box, Zap, Settings
} from 'lucide-react';
import { EvidenceModal } from '../EvidenceModal/EvidenceModal';
import './DocumentDetail.css';

interface DocumentDetailProps {
  document: Document;
  onClose: () => void;
}

export const DocumentDetail: React.FC<DocumentDetailProps> = ({ document, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'fields' | 'calculation'>('overview');
  const [selectedEvidence, setSelectedEvidence] = useState<any>(null);

  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)} minutes`;
    return `${hours.toFixed(1)} hours`;
  };

  const getFieldIcon = (fieldType: string) => {
    switch (fieldType) {
      case 'if': return <Code size={16} />;
      case 'precedentScript': return <FileText size={16} />;
      case 'reflection': return <Link size={16} />;
      case 'search': return <Search size={16} />;
      case 'unbound': return <Box size={16} />;
      case 'builtInScript': return <Zap size={16} />;
      case 'extended': return <Settings size={16} />;
      case 'scripted': return <Code size={16} />;
      default: return <Layers size={16} />;
    }
  };

  const getFieldLabel = (fieldType: string) => {
    const labels: Record<string, string> = {
      if: 'IF Statements',
      precedentScript: 'Precedent Scripts',
      reflection: 'Reflection Fields',
      search: 'Search Fields',
      unbound: 'Unbound Fields',
      builtInScript: 'Built-in Scripts',
      extended: 'Extended Fields',
      scripted: 'Scripted Fields'
    };
    return labels[fieldType] || fieldType;
  };

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-modal glass-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="detail-header">
          <div className="detail-title-group">
            <FileText size={24} className="detail-icon" />
            <div>
              <h2 className="headline-medium">{document.name}</h2>
              <p className="body-medium">{document.description}</p>
            </div>
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="detail-tabs">
          <button
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === 'fields' ? 'active' : ''}`}
            onClick={() => setActiveTab('fields')}
          >
            Field Analysis
          </button>
          <button
            className={`tab ${activeTab === 'calculation' ? 'active' : ''}`}
            onClick={() => setActiveTab('calculation')}
          >
            Calculation Details
          </button>
        </div>

        {/* Tab Content */}
        <div className="detail-content">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              {/* Key Metrics */}
              <div className="metrics-grid">
                <div className="metric-card glass-card">
                  <div className="metric-header">
                    <Layers size={20} />
                    <span className="label-large">Total Fields</span>
                  </div>
                  <div className="metric-value display-small">{document.totals.allFields}</div>
                  <div className="metric-details">
                    <div className="detail-row">
                      <span>Unique Fields</span>
                      <span>{document.totals.uniqueFields}</span>
                    </div>
                    <div className="detail-row">
                      <span>Reusable Fields</span>
                      <span>{document.totals.reusableFields}</span>
                    </div>
                  </div>
                </div>

                <div className="metric-card glass-card">
                  <div className="metric-header">
                    <Clock size={20} />
                    <span className="label-large">Effort Estimate</span>
                  </div>
                  <div className="metric-value display-small">{formatHours(document.effort.calculated)}</div>
                  <div className="metric-details">
                    <div className="detail-row">
                      <span>Optimized</span>
                      <span>{formatHours(document.effort.optimized)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Potential Savings</span>
                      <span className="savings">{formatHours(document.effort.savings)}</span>
                    </div>
                  </div>
                </div>

                <div className="metric-card glass-card">
                  <div className="metric-header">
                    <TrendingUp size={20} />
                    <span className="label-large">Reusability</span>
                  </div>
                  <div className="metric-value display-small">{document.totals.reuseRate}</div>
                  <div className="reuse-bar">
                    <div 
                      className="reuse-fill"
                      style={{ width: document.totals.reuseRate }}
                    />
                  </div>
                </div>
              </div>

              {/* Complexity Information */}
              <div className="complexity-section glass-card">
                <h3 className="title-large">Complexity Analysis</h3>
                <div className={`complexity-level complexity-${document.complexity.level.toLowerCase()}`}>
                  <span className="complexity-label">{document.complexity.level}</span>
                  <span className="complexity-reason body-medium">{document.complexity.reason}</span>
                </div>
                
                {/* Optional document structure - only show if data exists */}
                {(document.sections !== undefined || document.tables !== undefined || document.checkboxes !== undefined) && (
                  <div className="document-structure">
                    {document.sections !== undefined && (
                      <div className="structure-item">
                        <span>Sections</span>
                        <span>{document.sections}</span>
                      </div>
                    )}
                    {document.tables !== undefined && (
                      <div className="structure-item">
                        <span>Tables</span>
                        <span>{document.tables}</span>
                      </div>
                    )}
                    {document.checkboxes !== undefined && (
                      <div className="structure-item">
                        <span>Checkboxes</span>
                        <span>{document.checkboxes}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Evidence Source */}
              <div className="evidence-section glass-card">
                <h3 className="title-large">Data Source</h3>
                <div className="evidence-info">
                  <Database size={20} />
                  <div>
                    <p className="label-large">
                      {document.evidence.source || 'SQL Database'}
                    </p>
                    <p className="body-small">
                      Query: {document.evidence.query || 'SELECT * FROM documents'}
                    </p>
                    <p className="body-small">
                      Confidence: {document.evidence.confidence || 95}%
                    </p>
                    {document.evidence.traceability && (
                      <p className="body-small">
                        Analysis Date: {document.evidence.traceability.analysisDate || '2024-01-20'}
                      </p>
                    )}
                  </div>
                  <button
                    className="evidence-button"
                    onClick={() => setSelectedEvidence(document.evidence)}
                  >
                    <Info size={16} />
                    View Evidence
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'fields' && (
            <div className="fields-tab">
              <div className="fields-grid">
                {Object.entries(document.fields).map(([fieldType, metrics]) => (
                  <div key={fieldType} className="field-card glass-card">
                    <div className="field-header">
                      {getFieldIcon(fieldType)}
                      <span className="title-medium">{getFieldLabel(fieldType)}</span>
                    </div>
                    
                    <div className="field-stats">
                      <div className="stat-row">
                        <span className="label-small">Total Count</span>
                        <span className="body-large">{metrics.count}</span>
                      </div>
                      <div className="stat-row">
                        <span className="label-small">Unique</span>
                        <span className="body-medium">{metrics.unique}</span>
                      </div>
                      <div className="stat-row">
                        <span className="label-small">Reusable</span>
                        <span className="body-medium">{metrics.reusable}</span>
                      </div>
                      <div className="stat-row">
                        <span className="label-small">Reuse Rate</span>
                        <span className="body-medium reuse-rate">{metrics.reuseRate}</span>
                      </div>
                    </div>

                    <button
                      className="view-evidence-link"
                      onClick={() => setSelectedEvidence(metrics.evidence)}
                    >
                      <Info size={14} />
                      View Source
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'calculation' && (
            <div className="calculation-tab">
              {/* Effort Calculation */}
              <div className="calculation-section glass-card">
                <h3 className="title-large">Effort Calculation</h3>
                <div className="formula-display">
                  <code className="formula">{document.effort.calculation.formula}</code>
                </div>
                
                <div className="calculation-steps">
                  {document.effort.calculation.steps.map((step, index) => (
                    <div key={index} className="step">
                      <span className="step-number">{index + 1}</span>
                      <span className="step-label">{step.label}:</span>
                      <span className="step-value">
                        {typeof step.value === 'number' 
                          ? step.value.toFixed(2) 
                          : step.value}
                      </span>
                      {step.formula && (
                        <span className="step-formula">{step.formula}</span>
                      )}
                    </div>
                  ))}
                </div>
                
                <div className="calculation-result">
                  <span>Final Result:</span>
                  <span className="result-value">{formatHours(document.effort.calculation.result)}</span>
                </div>
              </div>

              {/* Complexity Calculation */}
              <div className="calculation-section glass-card">
                <h3 className="title-large">Complexity Determination</h3>
                <div className="formula-display">
                  <code className="formula">{document.complexity.calculation.formula}</code>
                </div>
                
                <div className="calculation-steps">
                  {document.complexity.calculation.steps.map((step, index) => (
                    <div key={index} className="step">
                      <span className="step-number">{index + 1}</span>
                      <span className="step-label">{step.label}:</span>
                      <span className="step-value">
                        {typeof step.value === 'number' 
                          ? step.value.toFixed(2) 
                          : step.value}
                      </span>
                      {step.formula && (
                        <span className="step-formula">{step.formula}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="detail-footer">
          <div className="footer-info">
            <span className="label-small">SQL File: {document.sqlFilename}</span>
            <span className="label-small">Document ID: {document.id}</span>
          </div>
        </div>
      </div>

      {/* Evidence Modal */}
      {selectedEvidence && (
        <EvidenceModal
          evidence={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
        />
      )}
    </div>
  );
};
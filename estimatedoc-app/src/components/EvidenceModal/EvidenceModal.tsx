import React from 'react';
import { X, Database, FileText, Copy, ExternalLink } from 'lucide-react';
import './EvidenceModal.css';

interface EvidenceModalProps {
  evidence: any;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ evidence, onClose }) => {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // In a real app, show a toast notification
  };

  return (
    <div className="evidence-overlay" onClick={onClose}>
      <div className="evidence-modal glass-modal" onClick={(e) => e.stopPropagation()}>
        <div className="evidence-header">
          <h2 className="headline-small">Evidence & Source Data</h2>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="evidence-content">
          {/* Source Information */}
          <div className="evidence-section">
            <div className="section-header">
              <Database size={18} />
              <h3 className="title-medium">Data Source</h3>
            </div>
            
            <div className="source-info">
              <div className="info-row">
                <span className="label">Source Type:</span>
                <span className="value">{evidence.source || 'SQL Database'}</span>
              </div>
              
              {evidence.files && (
                <div className="info-row">
                  <span className="label">Files:</span>
                  <div className="file-list">
                    {evidence.files.map((file: string, index: number) => (
                      <div key={index} className="file-item">
                        <FileText size={14} />
                        <span>{file}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {evidence.query && (
                <div className="query-section">
                  <div className="query-header">
                    <span className="label">Query:</span>
                    <button 
                      className="copy-button"
                      onClick={() => copyToClipboard(evidence.query)}
                      aria-label="Copy query"
                    >
                      <Copy size={14} />
                    </button>
                  </div>
                  <pre className="query-code">{evidence.query}</pre>
                </div>
              )}
            </div>
          </div>

          {/* Calculation Details */}
          {evidence.calculation && (
            <div className="evidence-section">
              <div className="section-header">
                <FileText size={18} />
                <h3 className="title-medium">Calculation Method</h3>
              </div>
              
              <div className="calculation-info">
                <pre className="calculation-formula">{evidence.calculation}</pre>
              </div>
            </div>
          )}

          {/* Trace Information */}
          {evidence.traceId && (
            <div className="evidence-section">
              <div className="section-header">
                <ExternalLink size={18} />
                <h3 className="title-medium">Audit Trail</h3>
              </div>
              
              <div className="trace-info">
                <div className="info-row">
                  <span className="label">Trace ID:</span>
                  <code className="trace-id">{evidence.traceId}</code>
                </div>
                
                {evidence.lastUpdated && (
                  <div className="info-row">
                    <span className="label">Last Updated:</span>
                    <span className="value">
                      {new Date(evidence.lastUpdated).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="evidence-footer">
          <p className="body-small">
            This data is sourced directly from the system database and calculations. 
            All values are traceable to their origin.
          </p>
        </div>
      </div>
    </div>
  );
};
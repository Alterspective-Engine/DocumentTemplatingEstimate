import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, BarChart2, Calculator, Activity } from 'lucide-react';
import { useDocumentStore } from '../../store/documentStore';
import './Header.css';

interface HeaderProps {
  onCalculatorOpen: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onCalculatorOpen }) => {
  const location = useLocation();
  const { documents } = useDocumentStore();

  return (
    <header className="app-header">
      <div className="header-container">
        <div className="header-brand">
          <img 
            src="/alterspective-logo.png" 
            alt="Alterspective" 
            className="brand-logo"
          />
          <div className="brand-divider"></div>
          <div className="app-info">
            <h1 className="app-title">EstimateDoc</h1>
            <p className="app-subtitle">Document Migration Effort Estimator</p>
          </div>
        </div>

        <nav className="header-nav">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            <FileText size={20} />
            <span>Documents</span>
          </Link>
          <Link 
            to="/statistics" 
            className={`nav-link ${location.pathname === '/statistics' ? 'active' : ''}`}
          >
            <BarChart2 size={20} />
            <span>Analytics</span>
          </Link>
          <button 
            className="nav-link calculator-btn"
            onClick={onCalculatorOpen}
          >
            <Calculator size={20} />
            <span>Calculator</span>
          </button>
        </nav>

        <div className="header-stats">
          <div className="stat-item">
            <Activity size={16} />
            <div className="stat-content">
              <span className="stat-value">{documents.length}</span>
              <span className="stat-label">Documents</span>
            </div>
          </div>
          <div className="stat-item">
            <div className="confidence-indicator">
              <span className="stat-value">99.6%</span>
              <span className="stat-label">Data Confidence</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
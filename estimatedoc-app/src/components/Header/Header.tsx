import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, BarChart2, Calculator, Activity, RefreshCw, Database, Upload } from 'lucide-react';
import { useDocumentStore } from '../../store/documentStore';
import './Header.css';

interface HeaderProps {
  // No props needed for now
}

export const Header: React.FC<HeaderProps> = () => {
  const location = useLocation();
  const { documents, dataSource, reloadDataFromSQL, isRecalculating } = useDocumentStore();
  const [isReloading, setIsReloading] = useState(false);
  const [isReprocessing, setIsReprocessing] = useState(false);

  const handleReloadData = async () => {
    setIsReloading(true);
    await reloadDataFromSQL();
    setIsReloading(false);
  };

  const handleReprocessData = async () => {
    // In browser environment, we can only reload the JSON data
    if (!confirm('This will reload data from the processed SQL JSON files.\nCalculator settings will be preserved.\nContinue?')) {
      return;
    }
    
    setIsReprocessing(true);
    try {
      // Since we're in the browser, just reload the page to get fresh data
      // The SQL JSON files are already processed and included in the build
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (error) {
      console.error('Reprocess error:', error);
      alert('Failed to reload data. Please refresh the page manually.');
    } finally {
      setTimeout(() => setIsReprocessing(false), 500);
    }
  };

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
          <Link 
            to="/calculator" 
            className={`nav-link ${location.pathname === '/calculator' ? 'active' : ''}`}
          >
            <Calculator size={20} />
            <span>Calculator</span>
          </Link>
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
            <Database size={16} />
            <div className="stat-content">
              <span className="stat-value">{dataSource}</span>
              <span className="stat-label">Data Source</span>
            </div>
          </div>
          <button
            className={`reload-button ${isReloading || isRecalculating ? 'loading' : ''}`}
            onClick={handleReloadData}
            disabled={isReloading || isRecalculating || isReprocessing}
            title="Reload data from current source"
          >
            <RefreshCw size={16} className={isReloading || isRecalculating ? 'spin' : ''} />
            <span>Reload</span>
          </button>
          <button
            className={`reprocess-button ${isReprocessing ? 'loading' : ''}`}
            onClick={handleReprocessData}
            disabled={isReloading || isRecalculating || isReprocessing}
            title="Reprocess all data from newSQL and ImportantData folders"
          >
            <Upload size={16} className={isReprocessing ? 'spin' : ''} />
            <span>Reprocess</span>
          </button>
        </div>
      </div>
    </header>
  );
};
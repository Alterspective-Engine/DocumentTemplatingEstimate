import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header/Header';
import { DocumentList } from './components/DocumentList/DocumentList';
import { Calculator } from './components/Calculator/Calculator';
import { Statistics } from './components/Statistics/Statistics';
import { lazy, Suspense } from 'react';
const CalculatorPage = lazy(() => import('./pages/CalculatorPage/CalculatorPage').then(m => ({ default: m.CalculatorPage })));
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
// Calculator functionality is now handled via routing
import { usePerformanceTracking, useErrorTracking } from './hooks/useAnalytics';
import { dataVerification } from './utils/dataVerification';
import { getShortVersion } from './config/version';
import './styles/theme.css';
import './App.css';

function App() {
  // Calculator functionality is now handled via routing
  
  // Initialize analytics tracking
  usePerformanceTracking();
  useErrorTracking();
  
  // Verify and fix data on initial load
  useEffect(() => {
    const verification = dataVerification.performFullVerification();
    
    if (verification.summary.failed > 0) {
      console.warn('Data inconsistencies detected, fixing...', verification.details);
      dataVerification.fixDataInconsistencies();
    } else {
      console.log('Data verification passed', verification.summary);
    }
  }, []);
  
  // Note: Live recalculation now happens when user clicks "Apply Settings" in Calculator
  // This provides visual feedback with updating animations on each card

  return (
    <ErrorBoundary>
      <Router>
        <div className="app">
          {/* Version display at top */}
          <div style={{
            position: 'fixed',
            top: '8px',
            right: '8px',
            fontSize: '12px',
            color: '#fff',
            backgroundColor: 'rgba(7, 81, 86, 0.9)',
            padding: '6px 12px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            zIndex: 10000,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            {getShortVersion()}
          </div>
          
          <Header />
          
          <main className="app-main">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<DocumentList />} />
                <Route path="/statistics" element={<Statistics />} />
                <Route path="/calculator" element={
                  <Suspense fallback={<div style={{ padding: '20px', textAlign: 'center' }}>Loading calculator...</div>}>
                    <CalculatorPage />
                  </Suspense>
                } />
              </Routes>
            </ErrorBoundary>
          </main>

          <Calculator />
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;

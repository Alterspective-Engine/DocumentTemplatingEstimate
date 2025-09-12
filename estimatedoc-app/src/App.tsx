import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header/Header';
import { DocumentList } from './components/DocumentList/DocumentList';
import { Calculator } from './components/Calculator/Calculator';
import { Statistics } from './components/Statistics/Statistics';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import { useCalculatorStore } from './store/calculatorStore';
import { useDocumentStore } from './store/documentStore';
import { usePerformanceTracking, useErrorTracking } from './hooks/useAnalytics';
import { dataVerification } from './utils/dataVerification';
import './styles/theme.css';
import './App.css';

function App() {
  const { openCalculator, settings } = useCalculatorStore();
  const { recalculateAllDocuments } = useDocumentStore();
  
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
          <Header onCalculatorOpen={openCalculator} />
          
          <main className="app-main">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<DocumentList />} />
                <Route path="/statistics" element={<Statistics />} />
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

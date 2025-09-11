import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header/Header';
import { DocumentList } from './components/DocumentList/DocumentList';
import { Calculator } from './components/Calculator/Calculator';
import { Statistics } from './components/Statistics/Statistics';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import { useCalculatorStore } from './store/calculatorStore';
import { usePerformanceTracking, useErrorTracking } from './hooks/useAnalytics';
import './styles/theme.css';
import './App.css';

function App() {
  const { openCalculator } = useCalculatorStore();
  
  // Initialize analytics tracking
  usePerformanceTracking();
  useErrorTracking();

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

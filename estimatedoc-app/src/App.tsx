import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header/Header';
import { DocumentList } from './components/DocumentList/DocumentList';
import { Calculator } from './components/Calculator/Calculator';
import { Statistics } from './components/Statistics/Statistics';
import { useCalculatorStore } from './store/calculatorStore';
import './styles/theme.css';
import './App.css';

function App() {
  const { openCalculator } = useCalculatorStore();

  return (
    <Router>
      <div className="app">
        <Header onCalculatorOpen={openCalculator} />
        
        <main className="app-main">
          <Routes>
            <Route path="/" element={<DocumentList />} />
            <Route path="/statistics" element={<Statistics />} />
          </Routes>
        </main>

        <Calculator />
      </div>
    </Router>
  );
}

export default App;

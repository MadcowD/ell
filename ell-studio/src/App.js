import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LMPList from './components/LMPList';
import LMPDetails from './components/LMPDetails';
import Traces from './components/Traces';
import { ThemeProvider } from './contexts/ThemeContext';
import './styles/globals.css';
import './styles/sourceCode.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="flex min-h-screen max-h-screen bg-gray-900 text-gray-100">
          <Sidebar />
          <div className="flex-1 flex flex-col max-h-screen overflow-hidden">
            <main className="flex-1 max-h-screen overflow-auto">
              <Routes>
                <Route path="/" element={<LMPList />} />
                <Route path="/lmp/:name/:id?" element={<LMPDetails />} />
                <Route path="/traces" element={<Traces />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
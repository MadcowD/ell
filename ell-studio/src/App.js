import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import LMP from './pages/LMP';
import Traces from './pages/Traces';
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
            <main className="flex-1 max-h-screen overflow-auto  hide-scrollbar">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/lmp/:name/:id?" element={<LMP />} />
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
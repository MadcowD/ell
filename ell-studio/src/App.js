import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LMPList from './components/LMPList';
import LMPDetails from './components/LMPDetails';
import { ThemeProvider } from './contexts/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="flex min-h-screen bg-gray-900 text-gray-100">
          <Sidebar />
          <div className="flex-1">
            <Header />
            <main className="container mx-auto px-6 py-8">
              <Routes>
                <Route path="/" element={<LMPList />} />
                <Route path="/lmp/:id" element={<LMPDetails />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
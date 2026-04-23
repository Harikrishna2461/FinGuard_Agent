import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Analytics from './pages/Analytics';
import SentimentAnalysis from './pages/SentimentAnalysis';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import Testing from './pages/Testing';
import AIAnalysis from './pages/AIAnalysis';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load user from localStorage or initialize
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      const newUser = {
        id: 'user_' + Date.now(),
        name: 'Investor',
        email: 'investor@finguard.com'
      };
      setUser(newUser);
      localStorage.setItem('user', JSON.stringify(newUser));
    }
    setLoading(false);
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-900 to-blue-700">
      <div className="text-white text-2xl font-bold">Loading FinGuard...</div>
    </div>;
  }

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <Navbar user={user} />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard user={user} />} />
            <Route path="/portfolio" element={<Portfolio user={user} />} />
            <Route path="/analytics" element={<Analytics user={user} />} />
            <Route path="/sentiment" element={<SentimentAnalysis user={user} />} />
            <Route path="/alerts" element={<Alerts user={user} />} />
            <Route path="/settings" element={<Settings user={user} />} />
            <Route path="/test" element={<Testing user={user} />} />
            <Route path="/ai-analysis" element={<AIAnalysis user={user} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

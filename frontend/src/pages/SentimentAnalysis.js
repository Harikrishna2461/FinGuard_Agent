import React, { useState, useEffect } from 'react';
import { FiRefreshCw, FiTrendingUp, FiTrendingDown } from 'react-icons/fi';
import './SentimentAnalysis.css';

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:15050`;

function SentimentAnalysis({ user }) {
  const [symbols, setSymbols] = useState([]);
  const [selectedSymbols, setSelectedSymbols] = useState(['AAPL']);
  const [sentimentData, setSentimentData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Load available symbols on component mount
  useEffect(() => {
    fetchSymbols();
  }, []);

  // Fetch sentiment when component loads or selected symbols change
  useEffect(() => {
    if (selectedSymbols.length > 0 && symbols.length > 0) {
      fetchSentiment();
    }
  }, [selectedSymbols, symbols]);

  const fetchSymbols = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/symbols`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) throw new Error('Failed to fetch symbols');
      
      const data = await response.json();
      
      if (data.symbols && Array.isArray(data.symbols)) {
        // Sort symbols alphabetically
        const sortedSymbols = data.symbols.sort((a, b) => 
          a.symbol.localeCompare(b.symbol)
        );
        setSymbols(sortedSymbols);
      } else {
        throw new Error('Invalid symbols response format');
      }
    } catch (err) {
      console.error('Error fetching symbols:', err);
      // Fallback to hardcoded symbols
      const fallbackSymbols = [
        { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
        { symbol: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology' },
        { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology' },
        { symbol: 'NVDA', name: 'NVIDIA Corporation', sector: 'Technology' },
        { symbol: 'META', name: 'Meta Platforms Inc.', sector: 'Technology' },
        { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Technology' },
        { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'Consumer' },
        { symbol: 'JPM', name: 'JPMorgan Chase & Co.', sector: 'Finance' },
        { symbol: 'JNJ', name: 'Johnson & Johnson', sector: 'Healthcare' },
        { symbol: 'WMT', name: 'Walmart Inc.', sector: 'Consumer' },
      ];
      setSymbols(fallbackSymbols);
    }
  };

  const fetchSentiment = async () => {
    setLoading(true);
    setError(null);
    try {
      const symbolsStr = selectedSymbols.join(',');
      const url = `${API_BASE_URL}/api/sentiment?symbols=${encodeURIComponent(symbolsStr)}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setSentimentData(data);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch sentiment data');
        setSentimentData(null);
      }
    } catch (err) {
      setError('Error fetching sentiment data: ' + err.message);
      setSentimentData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolToggle = (symbol) => {
    setSelectedSymbols(prev => {
      if (prev.includes(symbol)) {
        // Don't allow empty selection
        if (prev.length === 1) return prev;
        return prev.filter(s => s !== symbol);
      } else {
        // Max 10 symbols
        if (prev.length >= 10) {
          return [...prev.slice(1), symbol];
        }
        return [...prev, symbol];
      }
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSentiment();
    setRefreshing(false);
  };

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return '#94a3b8';
    const score = typeof sentiment === 'string' ? parseFloat(sentiment) : sentiment;
    if (score > 0.3) return '#10b981';
    if (score < -0.3) return '#ef4444';
    return '#f59e0b';
  };

  const getSentimentLabel = (sentiment) => {
    if (!sentiment) return 'Neutral';
    const score = typeof sentiment === 'string' ? parseFloat(sentiment) : sentiment;
    if (score > 0.3) return 'Bullish';
    if (score < -0.3) return 'Bearish';
    return 'Neutral';
  };

  return (
    <div className="sentiment-page">
      <div className="sentiment-header">
        <div>
          <h1>Market Sentiment Analysis</h1>
          <p>Track market sentiment for multiple stocks</p>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={handleRefresh}
          disabled={refreshing || loading}
        >
          <FiRefreshCw /> {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Symbol Selector */}
      <div className="symbol-selector card">
        <h3>Select Symbols to Analyze</h3>
        <div className="symbols-grid">
          {symbols.length > 0 ? (
            symbols.map((sym) => (
              <button
                key={sym.symbol}
                className={`symbol-chip ${selectedSymbols.includes(sym.symbol) ? 'active' : ''}`}
                onClick={() => handleSymbolToggle(sym.symbol)}
                title={sym.name}
              >
                {sym.symbol}
              </button>
            ))
          ) : (
            <p style={{ color: '#94a3b8', gridColumn: '1/-1' }}>Loading symbols...</p>
          )}
        </div>
        <div className="selected-info">
          <span className="selected-count">
            {selectedSymbols.length} symbol{selectedSymbols.length !== 1 ? 's' : ''} selected
          </span>
        </div>
      </div>

      {/* Sentiment Results */}
      {loading && (
        <div className="sentiment-loading">
          <div className="spinner"></div>
          <p>Analyzing market sentiment...</p>
        </div>
      )}

      {error && (
        <div className="error-message card">
          <strong>Error:</strong> {error}
          <p>Try selecting different symbols or refreshing the page</p>
        </div>
      )}

      {sentimentData && !loading && (
        <div className="sentiment-results">
          {/* Summary Stats */}
          <div className="sentiment-summary card">
            <h3>Sentiment Overview</h3>
            <div className="summary-grid">
              <div className="summary-stat">
                <div className="stat-label">Symbols Analyzed</div>
                <div className="stat-value">{selectedSymbols.length}</div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Bullish Count</div>
                <div className="stat-value" style={{ color: '#10b981' }}>
                  {selectedSymbols.filter(s => {
                    const sentimentText = sentimentData.sentiment_analysis || '';
                    return sentimentText.toLowerCase().includes(s.toLowerCase()) && 
                           sentimentText.toLowerCase().includes('bullish');
                  }).length || 0}
                </div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Bearish Count</div>
                <div className="stat-value" style={{ color: '#ef4444' }}>
                  {selectedSymbols.filter(s => {
                    const sentimentText = sentimentData.sentiment_analysis || '';
                    return sentimentText.toLowerCase().includes(s.toLowerCase()) && 
                           sentimentText.toLowerCase().includes('bearish');
                  }).length || 0}
                </div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Neutral Count</div>
                <div className="stat-value" style={{ color: '#f59e0b' }}>
                  {selectedSymbols.filter(s => {
                    const sentimentText = sentimentData.sentiment_analysis || '';
                    const isBullish = sentimentText.toLowerCase().includes(s.toLowerCase()) && 
                                     sentimentText.toLowerCase().includes('bullish');
                    const isBearish = sentimentText.toLowerCase().includes(s.toLowerCase()) && 
                                     sentimentText.toLowerCase().includes('bearish');
                    return !(isBullish || isBearish);
                  }).length || 0}
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Analysis */}
          <div className="sentiment-details card">
            <h3>Detailed Analysis</h3>
            <div className="analysis-text">
              <p>{sentimentData.sentiment_analysis || 'No sentiment data available'}</p>
            </div>
          </div>

          {/* Symbol Details */}
          <div className="symbol-details card">
            <h3>Symbol Sentiment Details</h3>
            <div className="symbol-list">
              {selectedSymbols.map((symbol) => (
                <div key={symbol} className="symbol-detail-item">
                  <div className="symbol-name">{symbol}</div>
                  <div className="symbol-sentiment">
                    <div 
                      className="sentiment-indicator"
                      style={{ backgroundColor: getSentimentColor(null) }}
                    >
                      {getSentimentLabel(null)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="recommendations card">
            <h3>AI Recommendations</h3>
            <div className="recommendation-list">
              <div className="recommendation-item">
                <div className="recommendation-icon">📊</div>
                <div className="recommendation-content">
                  <div className="recommendation-title">Portfolio Analysis</div>
                  <div className="recommendation-text">
                    Based on the sentiment analysis of {selectedSymbols.length} symbols, 
                    consider reviewing your holdings and diversification strategy.
                  </div>
                </div>
              </div>
              <div className="recommendation-item">
                <div className="recommendation-icon">⚡</div>
                <div className="recommendation-content">
                  <div className="recommendation-title">Trading Opportunity</div>
                  <div className="recommendation-text">
                    Current market sentiment shows mixed signals. Monitor closely before making significant trades.
                  </div>
                </div>
              </div>
              <div className="recommendation-item">
                <div className="recommendation-icon">🎯</div>
                <div className="recommendation-content">
                  <div className="recommendation-title">Risk Assessment</div>
                  <div className="recommendation-text">
                    Evaluate correlation between selected symbols to ensure proper portfolio diversification.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && !sentimentData && !error && symbols.length > 0 && (
        <div className="empty-state card">
          <div className="empty-icon">📈</div>
          <h3>No Sentiment Data Yet</h3>
          <p>Select one or more symbols above to get started with sentiment analysis</p>
        </div>
      )}
    </div>
  );
}

export default SentimentAnalysis;

import React, { useState, useEffect } from 'react';
import { FiRefreshCw } from 'react-icons/fi';
import ThinkingStream from '../components/ThinkingStream';
import './SentimentAnalysis.css';

function SentimentAnalysis({ user }) {
  const [symbols, setSymbols]               = useState([]);
  const [selectedSymbols, setSelectedSymbols] = useState(['AAPL']);
  const [sentimentData, setSentimentData]   = useState(null);
  const [loading, setLoading]               = useState(false);
  const [error, setError]                   = useState(null);
  const [streamUrl, setStreamUrl]           = useState(null);

  useEffect(() => { fetchSymbols(); }, []);

  const fetchSymbols = async () => {
    try {
      const res  = await fetch('/api/symbols');
      const data = await res.json();
      if (data.symbols && Array.isArray(data.symbols)) {
        setSymbols(data.symbols.sort((a, b) => a.symbol.localeCompare(b.symbol)));
      } else throw new Error('Bad response');
    } catch {
      setSymbols([
        { symbol: 'AAPL',  name: 'Apple Inc.',             sector: 'Technology' },
        { symbol: 'MSFT',  name: 'Microsoft Corporation',  sector: 'Technology' },
        { symbol: 'GOOGL', name: 'Alphabet Inc.',          sector: 'Technology' },
        { symbol: 'NVDA',  name: 'NVIDIA Corporation',     sector: 'Technology' },
        { symbol: 'META',  name: 'Meta Platforms Inc.',    sector: 'Technology' },
        { symbol: 'TSLA',  name: 'Tesla Inc.',             sector: 'Technology' },
        { symbol: 'AMZN',  name: 'Amazon.com Inc.',        sector: 'Consumer' },
        { symbol: 'JPM',   name: 'JPMorgan Chase & Co.',   sector: 'Finance' },
        { symbol: 'JNJ',   name: 'Johnson & Johnson',      sector: 'Healthcare' },
        { symbol: 'WMT',   name: 'Walmart Inc.',           sector: 'Consumer' },
      ]);
    }
  };

  const fetchSentiment = async () => {
    setLoading(true);
    setError(null);
    setSentimentData(null);
    setStreamUrl(null);

    try {
      const res  = await fetch('/api/sentiment/analyze', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ symbols: selectedSymbols }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to start analysis');
      setStreamUrl(`/api/sentiment/stream/${data.stream_id}`);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSymbolToggle = (symbol) => {
    setSelectedSymbols(prev => {
      if (prev.includes(symbol)) {
        if (prev.length === 1) return prev;
        return prev.filter(s => s !== symbol);
      }
      if (prev.length >= 10) return [...prev.slice(1), symbol];
      return [...prev, symbol];
    });
  };

  const getSentimentColor = (text, sym) => {
    if (!text) return '#94a3b8';
    const chunk = text.toLowerCase();
    const hasBullish = chunk.includes(sym.toLowerCase()) && chunk.includes('bullish');
    const hasBearish = chunk.includes(sym.toLowerCase()) && chunk.includes('bearish');
    if (hasBullish) return '#10b981';
    if (hasBearish) return '#ef4444';
    return '#f59e0b';
  };

  const getSentimentLabel = (text, sym) => {
    if (!text) return 'Neutral';
    const chunk = text.toLowerCase();
    if (chunk.includes(sym.toLowerCase()) && chunk.includes('bullish')) return 'Bullish';
    if (chunk.includes(sym.toLowerCase()) && chunk.includes('bearish')) return 'Bearish';
    return 'Neutral';
  };

  const sentimentText = sentimentData?.sentiment_analysis || '';

  return (
    <div className="sentiment-page">
      <div className="sentiment-header">
        <div>
          <h1>Market Sentiment Analysis</h1>
          <p>Track AI-powered market sentiment for multiple stocks</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={fetchSentiment}
          disabled={loading}
        >
          <FiRefreshCw /> {loading ? 'Analyzing…' : 'Analyze'}
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
            <p style={{ color: '#94a3b8', gridColumn: '1/-1' }}>Loading symbols…</p>
          )}
        </div>
        <div className="selected-info">
          <span className="selected-count">
            {selectedSymbols.length} symbol{selectedSymbols.length !== 1 ? 's' : ''} selected
          </span>
        </div>
      </div>

      {/* Live agent thinking */}
      <ThinkingStream
        streamUrl={streamUrl}
        onResult={(data) => { setSentimentData(data); setLoading(false); }}
        onError={(msg)  => { setError(msg); setLoading(false); }}
        onDone={()      => setLoading(false)}
      />

      {/* Error */}
      {error && (
        <div className="error-message card">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {sentimentData && !loading && (
        <div className="sentiment-results">
          <div className="sentiment-summary card">
            <h3>Sentiment Overview</h3>
            <div className="summary-grid">
              <div className="summary-stat">
                <div className="stat-label">Symbols Analyzed</div>
                <div className="stat-value">{selectedSymbols.length}</div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Bullish</div>
                <div className="stat-value" style={{ color: '#10b981' }}>
                  {selectedSymbols.filter(s => getSentimentLabel(sentimentText, s) === 'Bullish').length}
                </div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Bearish</div>
                <div className="stat-value" style={{ color: '#ef4444' }}>
                  {selectedSymbols.filter(s => getSentimentLabel(sentimentText, s) === 'Bearish').length}
                </div>
              </div>
              <div className="summary-stat">
                <div className="stat-label">Neutral</div>
                <div className="stat-value" style={{ color: '#f59e0b' }}>
                  {selectedSymbols.filter(s => getSentimentLabel(sentimentText, s) === 'Neutral').length}
                </div>
              </div>
            </div>
          </div>

          <div className="sentiment-details card">
            <h3>Detailed Analysis</h3>
            <div className="analysis-text">
              <p>{sentimentText || 'No sentiment data available'}</p>
            </div>
          </div>

          <div className="symbol-details card">
            <h3>Symbol Breakdown</h3>
            <div className="symbol-list">
              {selectedSymbols.map((symbol) => (
                <div key={symbol} className="symbol-detail-item">
                  <div className="symbol-name">{symbol}</div>
                  <div className="symbol-sentiment">
                    <div
                      className="sentiment-indicator"
                      style={{ backgroundColor: getSentimentColor(sentimentText, symbol) }}
                    >
                      {getSentimentLabel(sentimentText, symbol)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !sentimentData && !error && (
        <div className="empty-state card">
          <div className="empty-icon">📈</div>
          <h3>No Sentiment Data Yet</h3>
          <p>Select symbols above and click <strong>Analyze</strong> to get AI-powered market sentiment with live agent thinking</p>
        </div>
      )}
    </div>
  );
}

export default SentimentAnalysis;

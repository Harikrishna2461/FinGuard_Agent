import React, { useState, useRef, useEffect } from 'react';
import { FiSearch } from 'react-icons/fi';
import ThinkingStream from '../components/ThinkingStream';
import './Search.css';

function Search({ user }) {
  const [searchQuery, setSearchQuery] = useState('performance review');
  const [searchType, setSearchType] = useState('analyses');
  const [portfolioId, setPortfolioId] = useState('1');
  const [loading, setLoading] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [error, setError] = useState(null);
  const [streamUrl, setStreamUrl] = useState(null);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom when results change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [searchResult, error]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setSearchResult(null);
    setStreamUrl(null);

    try {
      const endpoint = searchType === 'market' 
        ? `/api/search/market`
        : `/api/search/${searchType}`;

      const payload = {
        query: searchQuery,
        ...(searchType !== 'market' && { portfolio_id: portfolioId })
      };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      
      // If guardrail blocked the query, IMMEDIATELY stop loading and show error
      if (!res.ok) {
        console.error('❌ Query blocked:', data.error);
        // Batch these updates together - loading goes false, error shows
        setLoading(false);
        setError(data.error || `Failed to start search (${res.status})`);
        setStreamUrl(null);
        return;
      }

      // Only set streamUrl if we got a successful response with stream_id
      if (!data.stream_id) {
        console.error('❌ No stream ID returned');
        setLoading(false);
        setError('No stream ID returned from server');
        setStreamUrl(null);
        return;
      }

      // Set up SSE stream for successful queries
      const streamPath = searchType === 'market'
        ? `/api/search/market/stream/${data.stream_id}`
        : `/api/search/${searchType}/stream/${data.stream_id}`;

      setStreamUrl(streamPath);
      // Don't clear loading here - let ThinkingStream's onDone clear it
    } catch (err) {
      console.error('❌ Fetch error:', err.message);
      setLoading(false);
      setError(`Network error: ${err.message}`);
      setStreamUrl(null);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleSearchTypeChange = (type) => {
    setSearchType(type);
    setStreamUrl(null);
    setSearchResult(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="search-page">
      {/* Header */}
      <div className="search-header">
        <div>
          <h1>Knowledge Search</h1>
          <p>Semantic search over past analyses, risks, and market data stored in ChromaDB</p>
        </div>
      </div>

      {/* Search Panel */}
      <div className="search-panel card">
        <div className="search-section">
          <h3>Search</h3>
          
          {/* Search Query Input */}
          <div className="search-input-group">
            <label className="form-label">Search Query</label>
            <textarea
              className="search-input"
              placeholder="Enter your search query..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              rows="3"
            />
          </div>

          {/* Search Type Selection */}
          <div className="search-options">
            <div className="search-type">
              <label className="form-label">Search In</label>
              <select 
                className="form-input" 
                value={searchType}
                onChange={(e) => handleSearchTypeChange(e.target.value)}
                disabled={loading}
              >
                <option value="analyses">Past Analyses</option>
                <option value="risks">Risk Assessments</option>
                <option value="market">Market Data</option>
              </select>
            </div>

            {searchType !== 'market' && (
              <div className="portfolio-select">
                <label className="form-label">Portfolio ID (optional)</label>
                <select 
                  className="form-input"
                  value={portfolioId}
                  onChange={(e) => setPortfolioId(e.target.value)}
                  disabled={loading}
                >
                  <option value="">Any</option>
                  <option value="1">Portfolio 1</option>
                  <option value="2">Portfolio 2</option>
                  <option value="3">Portfolio 3</option>
                </select>
              </div>
            )}
          </div>

          {/* Search Button */}
          <button 
            className="search-btn btn btn-primary"
            onClick={handleSearch}
            disabled={loading}
          >
            <FiSearch /> {loading ? 'Searching...' : 'Search'}
          </button>

          {/* Only show spinner if loading AND no error */}
          {loading && !error && (
            <div className="loading-indicator">
              <span className="spinner">⊙</span>
              <span>Searching...</span>
            </div>
          )}
        </div>
      </div>

      {/* Error Display - Shows immediately when query is blocked */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">✕</span>
          {error}
        </div>
      )}

      {/* Live Agent Thinking Stream - Only shows when actively streaming */}
      {streamUrl && !error && (
        <ThinkingStream
          streamUrl={streamUrl}
          onResult={(data) => {
            setSearchResult(data);
            setLoading(false);
          }}
          onError={(msg) => {
            setError(msg);
            setLoading(false);
          }}
          onDone={() => {
            setLoading(false);
          }}
        />
      )}

      {/* Search Results - Only show if we have results */}
      {searchResult && !error && (
        <div className="results-panel card">
          <h3>Results</h3>
          <div className="results-content">
            {searchResult.results && searchResult.results.length > 0 ? (
              <div className="results-list">
                {searchResult.results.map((result, idx) => (
                  <div key={idx} className="result-item">
                    <div className="result-header">
                      <h4>{result.title || result.metadata?.title || `Result ${idx + 1}`}</h4>
                      {result.metadata?.score && (
                        <span className="result-score">
                          Relevance: {(result.metadata.score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <div className="result-body">
                      {result.content || result.text || JSON.stringify(result, null, 2)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-results">No results found</p>
            )}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

export default Search;

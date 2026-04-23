import React, { useState, useRef, useEffect } from 'react';
import './AIAnalysis.css';

// ── Inline collapsible thinking block (like Claude.ai) ───────────────────────
function ThinkingBlock({ agent, thought, isLive }) {
  const [open, setOpen] = useState(true);
  return (
    <div className={`thinking-block ${isLive ? 'live' : 'done'}`}>
      <button className="thinking-header" onClick={() => setOpen(o => !o)}>
        <span className="thinking-dot" />
        <span className="thinking-agent">{agent}</span>
        <span className="thinking-label">{isLive ? 'thinking…' : 'thought for a moment'}</span>
        <span className="thinking-chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="thinking-body">
          <pre>{thought}</pre>
        </div>
      )}
    </div>
  );
}

// ── Crew status pill ──────────────────────────────────────────────────────────
function CrewBadge({ name, status }) {
  const cls = { waiting: 'badge-wait', running: 'badge-run', done: 'badge-done' }[status] || 'badge-wait';
  const icon = { waiting: '○', running: '●', done: '✓' }[status] || '○';
  return <span className={`crew-badge ${cls}`}>{icon} {name}</span>;
}

export default function AIAnalysis({ user }) {
  const [portfolioId, setPortfolioId]   = useState('1');
  const [isRunning, setIsRunning]       = useState(false);
  const [showThinking, setShowThinking] = useState(true);
  const [events, setEvents]             = useState([]);   // {type, agent?, crew?, thought?, output?}
  const [finalResult, setFinalResult]   = useState(null);
  const [error, setError]               = useState(null);
  const [crewStatus, setCrewStatus]     = useState({ 1: 'waiting', 2: 'waiting', 3: 'waiting' });
  const esRef = useRef(null);
  const bottomRef = useRef(null);

  // auto-scroll thinking log
  useEffect(() => {
    if (showThinking && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, showThinking]);

  const runAnalysis = async () => {
    setIsRunning(true);
    setEvents([]);
    setFinalResult(null);
    setError(null);
    setCrewStatus({ 1: 'waiting', 2: 'waiting', 3: 'waiting' });

    // Step 1 – start analysis, get stream_id
    let streamId;
    try {
      const res = await fetch(`/api/portfolio/${portfolioId}/analyze`, { method: 'POST' });
      if (!res.ok) { const j = await res.json(); throw new Error(j.error || 'Failed to start'); }
      const data = await res.json();
      streamId = data.stream_id;
    } catch (err) {
      setError(err.message);
      setIsRunning(false);
      return;
    }

    // Step 2 – open SSE stream
    const es = new EventSource(`/api/portfolio/${portfolioId}/analyze/stream/${streamId}`);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'heartbeat') return;

        if (msg.type === 'done') {
          es.close();
          setIsRunning(false);
          return;
        }

        if (msg.type === 'crew_start') {
          setCrewStatus(s => ({ ...s, [msg.data.crew]: 'running' }));
          setEvents(prev => [...prev, { type: 'crew_start', ...msg.data }]);
        }

        if (msg.type === 'agent_thinking') {
          setEvents(prev => [...prev, { type: 'thinking', agent: msg.data.agent, thought: msg.data.thought, crew: msg.data.crew }]);
        }

        if (msg.type === 'crew_done') {
          setCrewStatus(s => ({ ...s, [msg.data.crew]: 'done' }));
          setEvents(prev => [...prev, { type: 'crew_done', ...msg.data }]);
        }

        if (msg.type === 'result') {
          setFinalResult(msg.data);
          setIsRunning(false);
        }

        if (msg.type === 'error') {
          setError(msg.data.message);
          setIsRunning(false);
          es.close();
        }
      } catch {}
    };

    es.onerror = () => {
      es.close();
      setIsRunning(false);
    };
  };

  const stopAnalysis = () => {
    if (esRef.current) { esRef.current.close(); esRef.current = null; }
    setIsRunning(false);
  };

  const crewNames = { 1: 'Crew 1 · Risk Analysis', 2: 'Crew 2 · Portfolio', 3: 'Crew 3 · Summary' };

  return (
    <div className="ai-page">
      {/* ── Header ── */}
      <div className="ai-header">
        <div>
          <h1>🤖 AI Analysis</h1>
          <p>Run the full 9-agent CrewAI pipeline on a portfolio</p>
        </div>
        <div className="crew-status-row">
          {[1,2,3].map(n => <CrewBadge key={n} name={crewNames[n]} status={crewStatus[n]} />)}
        </div>
      </div>

      {/* ── Controls ── */}
      <div className="ai-controls">
        <div className="control-group">
          <label>Portfolio ID</label>
          <input
            value={portfolioId}
            onChange={e => setPortfolioId(e.target.value)}
            disabled={isRunning}
            placeholder="e.g. 1"
          />
        </div>

        <div className="control-group toggle-row">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={showThinking}
              onChange={e => setShowThinking(e.target.checked)}
            />
            Show agent thinking
          </label>
        </div>

        {!isRunning ? (
          <button className="btn-run" onClick={runAnalysis}>
            ▶ Run Full AI Analysis
          </button>
        ) : (
          <button className="btn-stop" onClick={stopAnalysis}>
            ⏹ Stop
          </button>
        )}
      </div>

      {/* ── Info banner ── */}
      <div className="agent-info-bar">
        Alert Intake → Customer Context → Risk Assessment → Explanation → Escalation → Portfolio Analysis → Risk Detection → Market Intelligence → Compliance
        <span className="warn-text">  ·  This may take 1–3 minutes</span>
      </div>

      {/* ── Live thinking stream ── */}
      {showThinking && events.length > 0 && (
        <div className="thinking-stream">
          {events.map((ev, i) => {
            if (ev.type === 'crew_start') return (
              <div key={i} className="crew-divider">
                ── Crew {ev.crew}: {ev.name} started · agents: {ev.agents?.join(', ')} ──
              </div>
            );
            if (ev.type === 'thinking') return (
              <ThinkingBlock key={i} agent={ev.agent} thought={ev.thought} isLive={isRunning && i === events.length - 1} />
            );
            if (ev.type === 'crew_done') return (
              <div key={i} className="crew-divider done">
                ✓ Crew {ev.crew}: {ev.name} completed
              </div>
            );
            return null;
          })}
          {isRunning && <div className="live-indicator">● live</div>}
          <div ref={bottomRef} />
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="error-box">❌ {error}</div>
      )}

      {/* ── Final Result ── */}
      {finalResult && (
        <div className="result-box">
          <div className="result-meta">
            ✅ Analysis Complete · Portfolio #{finalResult.portfolio_id} · {finalResult.agents_used} agents · {finalResult.crews_run} crews run · {new Date(finalResult.timestamp).toLocaleString()}
          </div>
          <div className="result-content markdown-output">
            {String(finalResult.crew_output)}
          </div>
          {finalResult.ml_prescreening && (
            <div className="ml-section">
              <strong>ML Pre-Screening:</strong>
              <pre>{finalResult.ml_prescreening}</pre>
            </div>
          )}
        </div>
      )}

      {/* ── Empty state ── */}
      {!isRunning && events.length === 0 && !finalResult && !error && (
        <div className="empty-state">
          Click <strong>Run Full AI Analysis</strong> to start the 9-agent crew pipeline
        </div>
      )}
    </div>
  );
}

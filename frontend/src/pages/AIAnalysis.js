import React, { useEffect, useState } from 'react';
import {
  FiAlertCircle,
  FiCheck,
  FiChevronUp,
  FiClock,
  FiLoader,
  FiPlay,
} from 'react-icons/fi';
import API_BASE_URL from '../config/api';
import './AIAnalysis.css';

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function formatPortfolioLine(portfolio, assets) {
  const name = portfolio?.name || 'Portfolio';
  const totalValue = Number(portfolio?.total_value || 0).toLocaleString();
  const symbols = assets.map((asset) => asset.symbol).filter(Boolean).slice(0, 6);
  return `Portfolio '${name}': $${totalValue} total, ${assets.length} assets, symbols: ${symbols.join(', ') || 'none'}`;
}

function buildRiskLines(transactions) {
  if (!transactions.length) {
    return ['No recent transactions found for this portfolio.'];
  }

  return transactions.slice(0, 5).map((txn, index) => {
    const amount = Number(txn.total_amount || txn.amount || 0).toFixed(2);
    return `Txn ${index + 1}: ${txn.type || 'unknown'} ${txn.symbol || 'n/a'} amount=$${amount} status=queued_for_hybrid_risk`;
  });
}

function normalizeError(error) {
  if (!error) return 'Analysis failed.';
  if (typeof error === 'string') return error;
  if (error.error) return error.error;
  if (typeof error.detail === 'string') return error.detail;
  if (error.detail?.error) return error.detail.error;
  return JSON.stringify(error);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(normalizeError(payload));
  }
  return payload;
}

function makeInitialEvents() {
  return [
    {
      id: 'ready',
      type: 'agent',
      name: 'Orchestrator',
      status: 'ready',
      state: 'done',
      body: 'Select a portfolio and start a full analysis to track each agent stage.',
    },
  ];
}

function makeTraceEvents(snapshot) {
  const portfolioLine = formatPortfolioLine(snapshot.portfolio, snapshot.assets);
  const txCount = snapshot.transactions.length;

  return [
    {
      id: 'risk-terminal',
      type: 'terminal',
      title: 'Transaction Risk Analysis',
      body: buildRiskLines(snapshot.transactions).join('\n'),
    },
    {
      id: 'crew-1-complete',
      type: 'divider',
      completed: true,
      label: 'Crew 1: Risk Analysis completed',
    },
    {
      id: 'risk-agent',
      type: 'agent',
      name: 'Risk Detection Agent',
      status: 'scanning',
      body: `Scanning transactions for fraud signals, velocity changes, unusual counterparties, and compliance flags...\n\n${txCount} transactions queued for review.`,
    },
    {
      id: 'crew-2-start',
      type: 'divider',
      label: 'Crew 2: Portfolio Analysis started - agents: Portfolio Analyst, Market Intelligence, Customer Context',
    },
    {
      id: 'portfolio-agent',
      type: 'agent',
      name: 'Portfolio Analyst',
      status: 'thinking',
      body: `Analyzing portfolio allocation and diversification:\n${portfolioLine}\n\nEvaluating asset weights, concentration risk, and rebalancing opportunities...`,
    },
    {
      id: 'market-agent',
      type: 'agent',
      name: 'Market Intelligence Agent',
      status: 'thinking',
      body: `Assessing market sentiment and trends for assets in portfolio:\n${portfolioLine}\n\nAnalyzing sentiment scores, trend signals, and investment recommendations...`,
    },
    {
      id: 'customer-agent',
      type: 'agent',
      name: 'Customer Context Agent',
      status: 'thinking',
      body: `Building customer context from portfolio and transaction history.\n\nRecent transactions: ${txCount}. Assets in scope: ${snapshot.assets.length}.`,
    },
    {
      id: 'crew-2-complete',
      type: 'divider',
      completed: true,
      label: 'Crew 2: Portfolio Analysis completed',
    },
    {
      id: 'crew-3-start',
      type: 'divider',
      label: 'Crew 3: Summary and Escalation started - agents: Alert Intake, Explanation, Escalation',
    },
    {
      id: 'alert-agent',
      type: 'agent',
      name: 'Alert Intake Agent',
      status: 'thinking',
      body: `Categorizing and prioritizing alerts from risk and portfolio outputs:\n${portfolioLine}\n\nDetermining severity, routing, and review requirements...`,
    },
    {
      id: 'explanation-agent',
      type: 'agent',
      name: 'Explanation Agent',
      status: 'thinking',
      body: 'Preparing analyst-readable rationale with the highest-impact risk, market, and portfolio signals.',
    },
    {
      id: 'escalation-agent',
      type: 'agent',
      name: 'Escalation Agent',
      status: 'thinking',
      body: 'Synthesizing all crew outputs into a final case summary and escalation recommendation...',
    },
  ];
}

function makeEventsFromAnalysisTrace(trace) {
  if (!Array.isArray(trace) || !trace.length) {
    return [];
  }

  return trace.map((event, index) => {
    const base = {
      id: `trace-${event.sequence || index + 1}`,
      type: event.type,
      node: event.node,
    };

    if (event.type === 'terminal') {
      return {
        ...base,
        title: event.title || event.node || 'LangGraph node',
        body: event.body || '',
      };
    }

    if (event.type === 'divider') {
      return {
        ...base,
        label: event.label || event.node || 'LangGraph stage',
        completed: event.completed !== false,
      };
    }

    const metadata = [
      event.node ? `node=${event.node}` : null,
      event.crew ? `crew=${event.crew}` : null,
      Number.isFinite(event.duration_ms) ? `duration_ms=${event.duration_ms}` : null,
    ].filter(Boolean);

    return {
      ...base,
      type: 'agent',
      name: event.name || event.agent || event.node || 'Agent',
      status: event.status || 'completed',
      body: metadata.length
        ? `${event.body || ''}\n\n${metadata.join(' | ')}`
        : event.body || '',
    };
  });
}

function AgentPanel({ agent, state }) {
  const isRunning = state === 'running';
  const isError = state === 'error' || agent.status === 'failed' || agent.status === 'rate_limited';
  const displayStatus = isRunning ? agent.status : agent.status || (state === 'done' ? 'completed' : 'queued');

  return (
    <section className={`agent-panel ${isRunning ? 'active' : ''} ${isError ? 'error' : ''}`}>
      <header className="agent-panel-header">
        <div className="agent-title">
          <span className={`agent-dot ${isRunning ? 'active' : ''} ${isError ? 'error' : ''}`} />
          <strong>{agent.name}</strong>
          <span>{displayStatus}</span>
        </div>
        <FiChevronUp />
      </header>
      <pre>{agent.body}</pre>
    </section>
  );
}

function CrewDivider({ event, state }) {
  const completed = event.completed || state === 'done';

  return (
    <div className={`crew-divider ${completed ? 'completed' : ''} ${state === 'running' ? 'active' : ''}`}>
      {completed ? <FiCheck /> : state === 'running' ? <FiLoader /> : <span />}
      <span>{event.label}</span>
    </div>
  );
}

function TerminalCard({ event }) {
  return (
    <section className="terminal-card">
      <div className="terminal-title">{event.title}</div>
      <pre>{event.body}</pre>
    </section>
  );
}

function ResultCard({ result }) {
  if (!result) return null;

  const output = result.crew_output || result.summary || result.recommendation || JSON.stringify(result, null, 2);
  return (
    <section className="terminal-card result-card">
      <div className="terminal-title">Final Analysis Result</div>
      <pre>{output}</pre>
    </section>
  );
}

function TraceEvent({ event, index, activeIndex, complete }) {
  const state = complete || index < activeIndex ? 'done' : index === activeIndex ? 'running' : 'queued';

  if (event.type === 'terminal') {
    return <TerminalCard event={event} />;
  }
  if (event.type === 'divider') {
    return <CrewDivider event={event} state={state} />;
  }
  return <AgentPanel agent={event} state={state} />;
}

function AIAnalysis() {
  const [portfolioId, setPortfolioId] = useState('');
  const [portfolios, setPortfolios] = useState([]);
  const [loadingPortfolios, setLoadingPortfolios] = useState(true);
  const [events, setEvents] = useState(makeInitialEvents);
  const [activeIndex, setActiveIndex] = useState(0);
  const [runState, setRunState] = useState('idle');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const isRunning = runState === 'running';
  const isComplete = runState === 'completed';
  const visibleEvents = isRunning || isComplete || runState === 'failed'
    ? events.slice(0, Math.min(activeIndex + 1, events.length))
    : events;

  useEffect(() => {
    let cancelled = false;

    const loadPortfolios = async () => {
      setLoadingPortfolios(true);
      try {
        const payload = await apiRequest('/api/portfolios');
        if (cancelled) return;

        const loadedPortfolios = payload.portfolios || [];
        setPortfolios(loadedPortfolios);
        setPortfolioId(loadedPortfolios[0]?.id ? String(loadedPortfolios[0].id) : '');
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to load portfolios.');
        }
      } finally {
        if (!cancelled) {
          setLoadingPortfolios(false);
        }
      }
    };

    loadPortfolios();

    return () => {
      cancelled = true;
    };
  }, []);

  const fetchSnapshot = async () => {
    const [portfolio, assetsPayload, transactionsPayload] = await Promise.all([
      apiRequest(`/api/portfolios/${portfolioId}`),
      apiRequest(`/api/portfolios/${portfolioId}/assets`),
      apiRequest(`/api/portfolios/${portfolioId}/transactions`),
    ]);

    return {
      portfolio,
      assets: assetsPayload.assets || [],
      transactions: transactionsPayload.transactions || [],
    };
  };

  const runAnalysis = async () => {
    if (isRunning) return;

    setRunState('running');
    setError('');
    setResult(null);
    setActiveIndex(0);

    try {
      const snapshot = await fetchSnapshot();
      const nextEvents = makeTraceEvents(snapshot);
      setEvents(nextEvents);

      const analysisPromise = apiRequest(`/api/portfolios/${portfolioId}/analyze`, {
        method: 'POST',
        body: JSON.stringify({}),
      });

      for (let index = 0; index < nextEvents.length; index += 1) {
        setActiveIndex(index);
        await wait(index === 0 ? 450 : 900);
      }

      const payload = await analysisPromise;
      const actualEvents = makeEventsFromAnalysisTrace(payload.analysis_trace);
      if (actualEvents.length) {
        setEvents(actualEvents);
        setActiveIndex(actualEvents.length);
      } else {
        setActiveIndex(nextEvents.length);
      }
      setResult(payload);
      setRunState('completed');
    } catch (err) {
      setError(err.message || 'Analysis failed.');
      setRunState('failed');
    }
  };

  return (
    <div className="ai-analysis-page">
      <div className="analysis-toolbar">
        <div>
          <h1>AI Analysis</h1>
          <p>Live multi-agent review for transaction, portfolio, and escalation workflows.</p>
        </div>
        <div className="analysis-actions">
          <label className="portfolio-field">
            <span>Portfolio</span>
            <select
              value={portfolioId}
              onChange={(event) => setPortfolioId(event.target.value)}
              disabled={isRunning || loadingPortfolios || !portfolios.length}
            >
              {loadingPortfolios && <option value="">Loading portfolios...</option>}
              {!loadingPortfolios && !portfolios.length && <option value="">No portfolios found</option>}
              {portfolios.map((portfolio) => (
                <option key={portfolio.id} value={portfolio.id}>
                  #{portfolio.id} - {portfolio.name} (${Number(portfolio.total_value || 0).toLocaleString()})
                </option>
              ))}
            </select>
          </label>
          <button className="run-analysis-btn" onClick={runAnalysis} disabled={isRunning || loadingPortfolios || !portfolioId}>
            {isRunning ? <FiLoader /> : <FiPlay />}
            {isRunning ? 'Running' : 'Run Analysis'}
          </button>
        </div>
      </div>

      <div className="analysis-stream">
        <div className="stream-header">
          <span><FiClock /> Orchestration trace</span>
          <span className={`stream-status ${runState}`}>
            {runState === 'failed' && <FiAlertCircle />}
            {runState === 'completed' && <FiCheck />}
            {runState.toUpperCase()}
          </span>
        </div>

        {error && (
          <div className="analysis-error">
            <FiAlertCircle />
            <span>{error}</span>
          </div>
        )}

        {visibleEvents.map((event, index) => (
          <TraceEvent
            key={event.id}
            event={event}
            index={index}
            activeIndex={activeIndex}
            complete={isComplete}
          />
        ))}

        {isComplete && <ResultCard result={result} />}
      </div>
    </div>
  );
}

export default AIAnalysis;

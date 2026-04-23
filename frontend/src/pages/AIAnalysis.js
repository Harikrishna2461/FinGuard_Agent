import React, { useState } from 'react';
import AgentThinking from '../components/AgentThinking';
import './AIAnalysis.css';

export default function AIAnalysis({ user }) {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [agentThinking, setAgentThinking] = useState('');
  const [portfolioId, setPortfolioId] = useState('1');
  const [showThinking, setShowThinking] = useState(true);

  const runFullAnalysis = async () => {
    setIsLoading(true);
    setAgentThinking('Initializing 9-agent CrewAI pipeline...\n\nStarting parallel crews:\n• Crew 1: Risk Analysis Agent → Compliance Agent → Detection Agent\n• Crew 2: Portfolio Analysis Agent\n• Crew 3: Market Intelligence Agent → Escalation Agent');

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));

      setAgentThinking(prev => prev + '\n\n✓ All agents completed analysis\n✓ Synthesizing results across crews...');

      // Mock result
      setResult({
        analysis_id: 'AN_' + Date.now(),
        portfolio_id: portfolioId,
        timestamp: new Date().toLocaleString(),
        crews: {
          crew_1: {
            name: 'Risk Analysis',
            agents: ['Risk Assessment', 'Compliance', 'Detection'],
            findings: [
              'No PDT violations detected',
              'No wash-sale violations',
              'Tax report for 2024: no capital gains or losses',
              'AML risk score: low',
              'No high-risk or critical transactions'
            ]
          },
          crew_2: {
            name: 'Portfolio Analysis',
            agents: ['Portfolio Analyst'],
            findings: [
              'Portfolio composition: Stocks 60%, Bonds 30%, Cash 10%',
              'Diversification score: 65/100',
              'Risk-adjusted return: 1.85 Sharpe ratio',
              'Recommended rebalancing: Increase bond allocation'
            ]
          },
          crew_3: {
            name: 'Market Intelligence',
            agents: ['Market Intel', 'Escalation'],
            findings: [
              'Market sentiment: Positive (0.6 score)',
              'Portfolio outlook: Stable with growth potential',
              'Escalation priority: Low',
              'Recommended action: Continue monitoring'
            ]
          }
        }
      });

      setAgentThinking(prev => prev + '\n\n📊 Analysis complete!');
    } catch (error) {
      setAgentThinking('❌ Error during analysis: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ai-analysis-page">
      <div className="analysis-header">
        <div>
          <h1>🤖 AI Analysis</h1>
          <p>Run the full 9-agent CrewAI pipeline on a portfolio</p>
        </div>
      </div>

      <div className="analysis-container">
        {/* Setup Panel */}
        <div className="setup-panel">
          <div className="setup-section">
            <label>Portfolio ID</label>
            <input
              type="text"
              value={portfolioId}
              onChange={(e) => setPortfolioId(e.target.value)}
              placeholder="Enter portfolio ID"
              disabled={isLoading}
            />
          </div>

          <div className="setup-section">
            <label>Analysis Type</label>
            <div className="analysis-info">
              <strong>Full Portfolio Analysis</strong>
              <small>This runs all 9 agents sequentially: Alert Intake → Customer Context → Risk Assessment → Explanation → Escalation → Portfolio Analysis → Risk Detection → Market Intelligence → Compliance. This may take 1-3 minutes.</small>
            </div>
          </div>

          <button
            className="btn btn-primary btn-large"
            onClick={runFullAnalysis}
            disabled={isLoading}
          >
            {isLoading ? '⏳ Running Analysis...' : '▶ Run Full AI Analysis'}
          </button>

          <div className="thinking-toggle">
            <label>
              <input
                type="checkbox"
                checked={showThinking}
                onChange={(e) => setShowThinking(e.target.checked)}
                disabled={isLoading}
              />
              Show Agent Thinking & Reasoning
            </label>
          </div>
        </div>

        {/* Main Content */}
        <div className="analysis-content">
          {/* Thinking Section */}
          {showThinking && (
            <AgentThinking
              agentName="Multi-Agent Crew"
              reasoning={agentThinking}
              isRunning={isLoading}
            />
          )}

          {/* Results Section */}
          {result && !isLoading && (
            <div className="results-section">
              <div className="result-header">
                <h2>✅ Analysis Complete</h2>
                <div className="result-meta">
                  <span>ID: {result.analysis_id}</span>
                  <span>•</span>
                  <span>Portfolio: {result.portfolio_id}</span>
                  <span>•</span>
                  <span>{result.timestamp}</span>
                </div>
              </div>

              {/* Crew Results */}
              <div className="crews-grid">
                {Object.values(result.crews).map((crew, idx) => (
                  <div key={idx} className="crew-card">
                    <h3>👥 {crew.name}</h3>
                    <div className="agents-list">
                      {crew.agents.map((agent, i) => (
                        <span key={i} className="agent-badge">
                          {agent}
                        </span>
                      ))}
                    </div>
                    <div className="findings">
                      <h4>Findings:</h4>
                      <ul>
                        {crew.findings.map((finding, i) => (
                          <li key={i}>{finding}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>

              {/* Summary */}
              <div className="summary-section">
                <h3>Summary</h3>
                <p>
                  The portfolio has been analyzed across 3 parallel crews (9 agents total)
                  for risk assessment, compliance, portfolio composition, and market outlook.
                  All analysis shows a low-risk profile with stable growth potential.
                </p>
              </div>
            </div>
          )}

          {!result && !isLoading && (
            <div className="empty-state">
              <p>👈 Click "Run Full AI Analysis" to start the 9-agent crew pipeline</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

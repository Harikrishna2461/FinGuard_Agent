import React, { useState, useEffect } from 'react';
import './AgentReasoning.css';

export default function AgentReasoning() {
  const [flows, setFlows] = useState([]);
  const [selectedFlow, setSelectedFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchFlows();
    const interval = autoRefresh ? setInterval(fetchFlows, 3000) : null;
    return () => interval && clearInterval(interval);
  }, [autoRefresh]);

  const fetchFlows = async () => {
    try {
      const response = await fetch('/api/agent/flows');
      const data = await response.json();
      setFlows(data.flows || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching flows:', error);
      setLoading(false);
    }
  };

  const fetchFlowDetails = async (flowId) => {
    try {
      const response = await fetch(`/api/agent/flows/${flowId}`);
      const data = await response.json();
      setSelectedFlow(data);
    } catch (error) {
      console.error('Error fetching flow details:', error);
    }
  };

  const handleFlowClick = (flow) => {
    fetchFlowDetails(flow.flow_id);
  };

  const getStatusColor = (status) => {
    return {
      completed: '#10b981',
      'in_progress': '#f59e0b',
      failed: '#ef4444',
    }[status] || '#6b7280';
  };

  const getStatusIcon = (status) => {
    return {
      completed: '✅',
      'in_progress': '⏳',
      failed: '❌',
    }[status] || '⚪';
  };

  return (
    <div className="agent-reasoning-container">
      <div className="reasoning-header">
        <h1>🤖 Agent Reasoning & Flow</h1>
        <p>Visualize how information flows through the multi-agent crew</p>
        <div className="controls">
          <button
            className={`refresh-btn ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '🔄 Auto-refresh ON' : '⏸️ Auto-refresh OFF'}
          </button>
          <button className="refresh-btn" onClick={fetchFlows}>
            🔄 Refresh Now
          </button>
        </div>
      </div>

      <div className="reasoning-content">
        <div className="flows-list">
          <h2>Recent Agent Flows</h2>
          {loading ? (
            <div className="loading">Loading flows...</div>
          ) : flows.length === 0 ? (
            <div className="no-data">No agent flows recorded yet</div>
          ) : (
            <div className="flows">
              {flows.map((flow) => (
                <div
                  key={flow.flow_id}
                  className={`flow-card ${selectedFlow?.flow_id === flow.flow_id ? 'selected' : ''}`}
                  onClick={() => handleFlowClick(flow)}
                >
                  <div className="flow-header">
                    <span className="status-icon">
                      {getStatusIcon(flow.status)}
                    </span>
                    <div className="flow-info">
                      <h3>{flow.flow_name}</h3>
                      <p className="flow-id">{flow.flow_id}</p>
                    </div>
                  </div>

                  <div className="flow-details">
                    <span className="step-count">
                      {flow.steps.length} steps
                    </span>
                    <span className="duration">
                      {flow.total_duration_ms.toFixed(0)}ms
                    </span>
                  </div>

                  <div className="agent-sequence">
                    {flow.agent_sequence.map((agent, idx) => (
                      <React.Fragment key={idx}>
                        <span className="agent-pill">{agent}</span>
                        {idx < flow.agent_sequence.length - 1 && (
                          <span className="arrow">→</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>

                  <div className="timestamp">
                    {new Date(flow.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flow-details-pane">
          {selectedFlow ? (
            <div className="details">
              <h2>{selectedFlow.flow_name}</h2>

              <div className="flow-overview">
                <div className="overview-item">
                  <label>Status</label>
                  <span
                    className="status-badge"
                    style={{ color: getStatusColor(selectedFlow.status) }}
                  >
                    {getStatusIcon(selectedFlow.status)} {selectedFlow.status}
                  </span>
                </div>
                <div className="overview-item">
                  <label>Total Duration</label>
                  <span>{selectedFlow.total_duration_ms.toFixed(2)}ms</span>
                </div>
                <div className="overview-item">
                  <label>Steps</label>
                  <span>{selectedFlow.steps.length}</span>
                </div>
              </div>

              <div className="agent-pipeline">
                <h3>Agent Pipeline</h3>
                <div className="pipeline">
                  {selectedFlow.steps.map((step, idx) => (
                    <div key={idx} className="pipeline-stage">
                      <div className="agent-box">
                        <div className="agent-name">{step.agent_name}</div>
                        <div className="step-number">Step {step.step_number}</div>
                      </div>

                      <div className="stage-details">
                        <div className="detail-section">
                          <h4>Input</h4>
                          <pre className="data-display">
                            {JSON.stringify(step.input_data, null, 2)}
                          </pre>
                        </div>

                        <div className="detail-section">
                          <h4>Reasoning</h4>
                          <p className="reasoning-text">
                            {step.reasoning}
                          </p>
                        </div>

                        <div className="detail-section">
                          <h4>Output</h4>
                          <pre className="data-display">
                            {JSON.stringify(step.output_data, null, 2)}
                          </pre>
                        </div>

                        <div className="step-meta">
                          <span>⏱️ {step.duration_ms.toFixed(2)}ms</span>
                          <span>🕒 {new Date(step.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>

                      {idx < selectedFlow.steps.length - 1 && (
                        <div className="pipeline-arrow">↓</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="json-export">
                <h3>Full Flow Data (JSON)</h3>
                <pre>
                  {JSON.stringify(selectedFlow, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="no-selection">
              <p>👈 Select a flow to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

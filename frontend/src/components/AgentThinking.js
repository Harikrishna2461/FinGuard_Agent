import React, { useState } from 'react';
import './AgentThinking.css';

/**
 * AgentThinking component - shows/hides agent reasoning inline
 * Usage: <AgentThinking reasoning={agentReasoning} isRunning={true} />
 */
export default function AgentThinking({ reasoning, isRunning = false, agentName = "Agent" }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!reasoning && !isRunning) return null;

  return (
    <div className={`agent-thinking ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <button
        className="thinking-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="thinking-icon">
          {isRunning ? '🤔' : '💡'}
        </span>
        <span className="thinking-label">
          {isRunning ? `${agentName} is thinking...` : `${agentName}'s reasoning`}
        </span>
        <span className="toggle-icon">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>

      {isExpanded && (
        <div className="thinking-content">
          {isRunning ? (
            <div className="thinking-spinner">
              <div className="spinner"></div>
              <p>Agent is processing...</p>
            </div>
          ) : reasoning ? (
            <div className="thinking-text">
              {reasoning}
            </div>
          ) : (
            <p className="thinking-empty">No reasoning available</p>
          )}
        </div>
      )}
    </div>
  );
}

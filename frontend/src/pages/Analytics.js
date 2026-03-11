import React, { useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FiRefreshCw, FiDownload } from 'react-icons/fi';
import './Analytics.css';

function Analytics({ user }) {
  const [timeframe, setTimeframe] = useState('1M');

  const performanceData = [
    { month: 'Jan', return: 2.5, benchmark: 1.8 },
    { month: 'Feb', return: 3.2, benchmark: 2.1 },
    { month: 'Mar', return: 1.8, benchmark: 2.5 },
    { month: 'Apr', return: 4.2, benchmark: 3.0 },
    { month: 'May', return: 5.1, benchmark: 3.8 },
  ];

  const riskMetrics = [
    { name: 'Volatility Risk', value: 35, color: '#ef4444' },
    { name: 'Concentration Risk', value: 25, color: '#f59e0b' },
    { name: 'Market Risk', value: 30, color: '#3b82f6' },
    { name: 'Liquidity Risk', value: 10, color: '#10b981' },
  ];

  const sectorAnalysis = [
    { sector: 'Technology', allocation: 40, performance: 5.8 },
    { sector: 'Healthcare', allocation: 25, performance: 3.2 },
    { sector: 'Finance', allocation: 20, performance: 2.5 },
    { sector: 'Utilities', allocation: 10, performance: 1.8 },
    { sector: 'Other', allocation: 5, performance: -0.5 },
  ];

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <div>
          <h1>Portfolio Analytics</h1>
          <p>Advanced insights and performance analysis</p>
        </div>
        <div className="header-actions">
          <select className="timeframe-select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            <option value="1W">1 Week</option>
            <option value="1M">1 Month</option>
            <option value="3M">3 Months</option>
            <option value="1Y">1 Year</option>
            <option value="ALL">All Time</option>
          </select>
          <button className="btn btn-sm btn-primary">
            <FiDownload /> Export Report
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Sharpe Ratio</div>
          <div className="metric-value">1.85</div>
          <div className="metric-sub">Risk-adjusted return</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Max Drawdown</div>
          <div className="metric-value">-8.5%</div>
          <div className="metric-sub">Peak to trough decline</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Win Rate</div>
          <div className="metric-value">68.5%</div>
          <div className="metric-sub">Profitable months</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Correlation</div>
          <div className="metric-value">0.72</div>
          <div className="metric-sub">Market correlation</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* Performance vs Benchmark */}
        <div className="chart-card">
          <h3>Performance vs Benchmark</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="month" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Tooltip
                contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
              <Line type="monotone" dataKey="return" stroke="#10b981" strokeWidth={2} name="Portfolio Return" />
              <Line type="monotone" dataKey="benchmark" stroke="#94a3b8" strokeWidth={2} name="Benchmark" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Breakdown */}
        <div className="chart-card">
          <h3>Risk Assessment</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskMetrics}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskMetrics.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Performance */}
        <div className="chart-card full-width">
          <h3>Sector Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sectorAnalysis}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="sector" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" yAxisId="left" />
              <YAxis stroke="#cbd5e1" yAxisId="right" orientation="right" />
              <Tooltip
                contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Legend />
              <Bar dataKey="allocation" fill="#3b82f6" yAxisId="left" name="Allocation %" />
              <Bar dataKey="performance" fill="#10b981" yAxisId="right" name="Performance %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recommendations */}
      <div className="recommendations card">
        <h3>AI Recommendations</h3>
        <div className="recommendation-list">
          <div className="recommendation-item">
            <div className="recommendation-icon">⚡</div>
            <div className="recommendation-content">
              <div className="recommendation-title">Rebalance Portfolio</div>
              <div className="recommendation-text">Your tech allocation has grown to 45%. Consider rebalancing to target 40%.</div>
            </div>
            <button className="btn btn-sm btn-primary">Review</button>
          </div>
          <div className="recommendation-item">
            <div className="recommendation-icon">🎯</div>
            <div className="recommendation-content">
              <div className="recommendation-title">Opportunity: NVDA Entry Point</div>
              <div className="recommendation-text">Recently corrected 12%. AI signal: Strong buy at current levels.</div>
            </div>
            <button className="btn btn-sm btn-primary">Analyze</button>
          </div>
          <div className="recommendation-item">
            <div className="recommendation-icon">🛡️</div>
            <div className="recommendation-content">
              <div className="recommendation-title">Risk Mitigation</div>
              <div className="recommendation-text">Consider adding defensive positions. Market volatility index rising.</div>
            </div>
            <button className="btn btn-sm btn-primary">Explore</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Analytics;

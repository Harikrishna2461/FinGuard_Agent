import React, { useState, useEffect } from 'react';
import { FiArrowUp, FiRefreshCw } from 'react-icons/fi';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './Dashboard.css';

function Dashboard({ user }) {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize with demo data
    setTimeout(() => {
      setPortfolioData({
        totalValue: 125450.89,
        cashBalance: 15230.50,
        dayChange: 2340.50,
        dayChangePercent: 1.89,
        yearYield: 22.5,
        assets: [
          { symbol: 'AAPL', name: 'Apple', quantity: 50, price: 189.50, value: 9475, change: 2.5 },
          { symbol: 'MSFT', name: 'Microsoft', quantity: 30, price: 378.90, value: 11367, change: 1.8 },
          { symbol: 'GOOGL', name: 'Google', quantity: 20, price: 139.80, value: 2796, change: 3.2 },
          { symbol: 'TSLA', name: 'Tesla', quantity: 15, price: 242.50, value: 3637.5, change: -1.5 },
          { symbol: 'AMZN', name: 'Amazon', quantity: 10, price: 172.30, value: 1723, change: 0.5 },
          { symbol: 'NVDA', name: 'NVIDIA', quantity: 8, price: 875.20, value: 7001.6, change: 4.2 },
        ],
        chartData: [
          { date: 'Jan 1', value: 95000 },
          { date: 'Jan 15', value: 98500 },
          { date: 'Feb 1', value: 102000 },
          { date: 'Feb 15', value: 99800 },
          { date: 'Mar 1', value: 105300 },
          { date: 'Mar 15', value: 108900 },
          { date: 'Apr 1', value: 112400 },
          { date: 'Apr 15', value: 115800 },
          { date: 'May 1', value: 118200 },
          { date: 'May 15', value: 125450.89 },
        ],
        dailyReturns: [
          { date: 'Mon', return: 0.5 },
          { date: 'Tue', return: -0.2 },
          { date: 'Wed', return: 1.2 },
          { date: 'Thu', return: 0.8 },
          { date: 'Fri', return: 1.5 },
          { date: 'Mon', return: 0.3 },
          { date: 'Tue', return: -0.5 },
        ],
        allocation: [
          { name: 'Stocks', value: 75, color: '#3b82f6' },
          { name: 'Cash', value: 15, color: '#10b981' },
          { name: 'ETFs', value: 7, color: '#f59e0b' },
          { name: 'Crypto', value: 3, color: '#8b5cf6' },
        ],
      });
      setLoading(false);
    }, 500);
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1000);
  };

  if (loading) {
    return <div className="dashboard-loading">Loading portfolio data...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Welcome back, {user?.name}!</h1>
          <p>Here's your financial overview</p>
        </div>
        <button className="refresh-btn" onClick={handleRefresh}>
          <FiRefreshCw /> Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Portfolio Value</div>
          <div className="metric-value">${portfolioData?.totalValue.toFixed(2)}</div>
          <div className="metric-sub">
            <span className="positive">
              <FiArrowUp /> ${portfolioData?.dayChange.toFixed(2)} ({portfolioData?.dayChangePercent}%)
            </span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Cash Balance</div>
          <div className="metric-value">${portfolioData?.cashBalance.toFixed(2)}</div>
          <div className="metric-sub">Available for trading</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Year-to-Date Return</div>
          <div className="metric-value positive-text">{portfolioData?.yearYield}%</div>
          <div className="metric-sub">Investment performance</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Assets Held</div>
          <div className="metric-value">{portfolioData?.assets.length}</div>
          <div className="metric-sub">Actively traded</div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        {/* Portfolio Value Trend */}
        <div className="chart-card">
          <h3>Portfolio Value Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={portfolioData?.chartData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="date" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Tooltip
                contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area type="monotone" dataKey="value" stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Returns */}
        <div className="chart-card">
          <h3>Daily Returns</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={portfolioData?.dailyReturns}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
              <XAxis dataKey="date" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Tooltip
                contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(148, 163, 184, 0.2)', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="return" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Asset Allocation & Holdings */}
      <div className="holdings-section">
        <div className="allocation-card chart-card">
          <h3>Asset Allocation</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={portfolioData?.allocation}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {portfolioData?.allocation.map((entry, index) => (
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

        <div className="holdings-card chart-card">
          <h3>Top Holdings</h3>
          <div className="holdings-list">
            {portfolioData?.assets.map((asset, idx) => (
              <div key={idx} className="holding-item">
                <div className="holding-info">
                  <div className="holding-symbol">{asset.symbol}</div>
                  <div className="holding-name">{asset.name}</div>
                </div>
                <div className="holding-stats">
                  <div className="holding-value">${asset.value.toFixed(2)}</div>
                  <div className={`holding-change ${asset.change > 0 ? 'positive' : 'negative'}`}>
                    {asset.change > 0 ? '+' : ''}{asset.change}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      <div className="alerts-section card">
        <h3>Recent Alerts</h3>
        <div className="alerts-list">
          <div className="alert-item alert-warning">
            <span className="alert-icon">⚠️</span>
            <div className="alert-content">
              <div className="alert-title">Market Volatility Alert</div>
              <div className="alert-message">TSLA showing high volatility - consider hedging strategies</div>
            </div>
          </div>
          <div className="alert-item alert-info">
            <span className="alert-icon">ℹ️</span>
            <div className="alert-content">
              <div className="alert-title">Earnings Coming</div>
              <div className="alert-message">AAPL earnings report expected in 3 days</div>
            </div>
          </div>
          <div className="alert-item alert-success">
            <span className="alert-icon">✓</span>
            <div className="alert-content">
              <div className="alert-title">Target Reached</div>
              <div className="alert-message">MSFT hit your target price of $380</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

import React, { useState } from 'react';
import { FiX, FiPlus, FiEdit2, FiToggle2, FiBell } from 'react-icons/fi';
import './Alerts.css';

function Alerts({ user }) {
  const [alerts, setAlerts] = useState([
    { id: 1, type: 'price', symbol: 'AAPL', title: 'AAPL Target Price', condition: 'Price > $200', isActive: true, triggered: false },
    { id: 2, type: 'performance', symbol: 'Portfolio', title: 'Daily Loss Alert', condition: 'Loss > 2%', isActive: true, triggered: false },
    { id: 3, type: 'volatility', symbol: 'TSLA', title: 'TSLA High Volatility', condition: 'Volatility > 4%', isActive: true, triggered: true },
    { id: 4, type: 'news', symbol: 'MSFT', title: 'MSFT News Alert', condition: 'Major announcement', isActive: false, triggered: false },
  ]);

  const [showForm, setShowForm] = useState(false);
  const [newAlert, setNewAlert] = useState({ type: 'price', symbol: '', title: '', condition: '' });

  const handleAddAlert = (e) => {
    e.preventDefault();
    const alert = {
      id: Date.now(),
      ...newAlert,
      isActive: true,
      triggered: false
    };
    setAlerts([...alerts, alert]);
    setNewAlert({ type: 'price', symbol: '', title: '', condition: '' });
    setShowForm(false);
  };

  const handleToggleAlert = (id) => {
    setAlerts(alerts.map(alert => alert.id === id ? { ...alert, isActive: !alert.isActive } : alert));
  };

  const handleDeleteAlert = (id) => {
    setAlerts(alerts.filter(alert => alert.id !== id));
  };

  const getAlertIcon = (type) => {
    const icons = {
      price: '📈',
      performance: '📊',
      volatility: '⚡',
      news: '📰',
      fraud: '🚨'
    };
    return icons[type] || '🔔';
  };

  const getAlertColor = (triggered) => {
    return triggered ? 'triggered' : 'pending';
  };

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <div>
          <h1>Alerts & Notifications</h1>
          <p>Manage your portfolio alerts and notifications</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <FiPlus /> Create Alert
        </button>
      </div>

      {/* Alert Statistics */}
      <div className="alert-stats">
        <div className="stat-card">
          <div className="stat-number">{alerts.length}</div>
          <div className="stat-label">Total Alerts</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{alerts.filter(a => a.isActive).length}</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{alerts.filter(a => a.triggered).length}</div>
          <div className="stat-label">Triggered</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{alerts.filter(a => !a.isActive).length}</div>
          <div className="stat-label">Disabled</div>
        </div>
      </div>

      {/* Create Alert Form */}
      {showForm && (
        <div className="create-alert card">
          <h3>Create New Alert</h3>
          <form onSubmit={handleAddAlert}>
            <div className="form-group">
              <label className="form-label">Alert Type</label>
              <select
                className="form-input"
                value={newAlert.type}
                onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value })}
                required
              >
                <option value="price">Price Alert</option>
                <option value="performance">Performance Alert</option>
                <option value="volatility">Volatility Alert</option>
                <option value="news">News Alert</option>
                <option value="fraud">Fraud Detection</option>
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., AAPL"
                  value={newAlert.symbol}
                  onChange={(e) => setNewAlert({ ...newAlert, symbol: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Title</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Alert name"
                  value={newAlert.title}
                  onChange={(e) => setNewAlert({ ...newAlert, title: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Trigger Condition</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Price > $150"
                value={newAlert.condition}
                onChange={(e) => setNewAlert({ ...newAlert, condition: e.target.value })}
                required
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Create Alert</button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Alerts List */}
      <div className="alerts-list">
        {alerts.map((alert) => (
          <div key={alert.id} className={`alert-card ${getAlertColor(alert.triggered)}`}>
            <div className="alert-icon">{getAlertIcon(alert.type)}</div>
            <div className="alert-details">
              <div className="alert-title">{alert.title}</div>
              <div className="alert-symbol">{alert.symbol}</div>
              <div className="alert-condition">{alert.condition}</div>
            </div>
            <div className="alert-status">
              {alert.triggered && <span className="badge badge-danger">Triggered</span>}
              {!alert.isActive && <span className="badge">Disabled</span>}
              {alert.isActive && !alert.triggered && <span className="badge badge-success">Active</span>}
            </div>
            <div className="alert-actions">
              <button
                className="action-btn toggle"
                title={alert.isActive ? 'Disable' : 'Enable'}
                onClick={() => handleToggleAlert(alert.id)}
              >
                <FiToggle2 />
              </button>
              <button className="action-btn edit" title="Edit">
                <FiEdit2 />
              </button>
              <button
                className="action-btn delete"
                title="Delete"
                onClick={() => handleDeleteAlert(alert.id)}
              >
                <FiX />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Alert History */}
      <div className="alert-history card">
        <h3>Recent Triggered Alerts</h3>
        <div className="history-list">
          <div className="history-item">
            <div className="history-icon">⚡</div>
            <div className="history-content">
              <div className="history-title">TSLA High Volatility Triggered</div>
              <div className="history-time">2 minutes ago</div>
            </div>
          </div>
          <div className="history-item">
            <div className="history-icon">📈</div>
            <div className="history-content">
              <div className="history-title">AAPL Target Price Reached</div>
              <div className="history-time">1 hour ago</div>
            </div>
          </div>
          <div className="history-item">
            <div className="history-icon">📊</div>
            <div className="history-content">
              <div className="history-title">Daily Gain Alert Triggered</div>
              <div className="history-time">5 hours ago</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Alerts;

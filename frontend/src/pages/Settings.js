import React, { useState } from 'react';
import { FiSave, FiLock, FiBell, FiUser, FiCreditCard } from 'react-icons/fi';
import './Settings.css';

function Settings({ user }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState({
    fullName: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 (555) 123-4567',
    riskProfile: 'moderate'
  });

  const [preferences, setPreferences] = useState({
    emailAlerts: true,
    priceAlerts: true,
    performanceAlerts: true,
    newsAlerts: false,
    dailyReport: true,
    reportTime: '09:00',
    currency: 'USD',
    language: 'English'
  });

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    loginAlerts: true,
    sessionTimeout: '30',
    lastPasswordChange: '2024-01-15'
  });

  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleProfileChange = (field, value) => {
    setProfile({ ...profile, [field]: value });
    setSaveSuccess(false);
  };

  const handlePreferenceChange = (field, value) => {
    setPreferences({ ...preferences, [field]: value });
    setSaveSuccess(false);
  };

  const handleSecurityChange = (field, value) => {
    setSecurity({ ...security, [field]: value });
    setSaveSuccess(false);
  };

  const handleSave = () => {
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Manage your account and preferences</p>
      </div>

      {saveSuccess && <div className="alert alert-success">✓ Settings saved successfully!</div>}

      <div className="settings-container">
        {/* Sidebar Tabs */}
        <div className="settings-sidebar">
          <button
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            <FiUser /> Profile
          </button>
          <button
            className={`tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            <FiBell /> Preferences
          </button>
          <button
            className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            <FiLock /> Security
          </button>
          <button
            className={`tab-btn ${activeTab === 'billing' ? 'active' : ''}`}
            onClick={() => setActiveTab('billing')}
          >
            <FiCreditCard /> Billing
          </button>
        </div>

        {/* Content Area */}
        <div className="settings-content">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="tab-content card">
              <h2>Profile Information</h2>
              <div className="settings-form">
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={profile.fullName}
                    onChange={(e) => handleProfileChange('fullName', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-input"
                    value={profile.email}
                    onChange={(e) => handleProfileChange('email', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Phone Number</label>
                  <input
                    type="tel"
                    className="form-input"
                    value={profile.phone}
                    onChange={(e) => handleProfileChange('phone', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Risk Profile</label>
                  <select
                    className="form-input"
                    value={profile.riskProfile}
                    onChange={(e) => handleProfileChange('riskProfile', e.target.value)}
                  >
                    <option value="conservative">Conservative</option>
                    <option value="moderate">Moderate</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </div>

                <button className="btn btn-primary" onClick={handleSave}>
                  <FiSave /> Save Changes
                </button>
              </div>
            </div>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="tab-content card">
              <h2>Notification Preferences</h2>
              <div className="preferences-section">
                <h3>Alert Notifications</h3>
                <div className="toggle-group">
                  <div className="toggle-item">
                    <div className="toggle-info">
                      <div className="toggle-title">Email Alerts</div>
                      <div className="toggle-desc">Receive alerts via email</div>
                    </div>
                    <input
                      type="checkbox"
                      className="toggle-checkbox"
                      checked={preferences.emailAlerts}
                      onChange={(e) => handlePreferenceChange('emailAlerts', e.target.checked)}
                    />
                  </div>

                  <div className="toggle-item">
                    <div className="toggle-info">
                      <div className="toggle-title">Price Alerts</div>
                      <div className="toggle-desc">Get notified when prices reach targets</div>
                    </div>
                    <input
                      type="checkbox"
                      className="toggle-checkbox"
                      checked={preferences.priceAlerts}
                      onChange={(e) => handlePreferenceChange('priceAlerts', e.target.checked)}
                    />
                  </div>

                  <div className="toggle-item">
                    <div className="toggle-info">
                      <div className="toggle-title">Performance Alerts</div>
                      <div className="toggle-desc">Daily portfolio performance notifications</div>
                    </div>
                    <input
                      type="checkbox"
                      className="toggle-checkbox"
                      checked={preferences.performanceAlerts}
                      onChange={(e) => handlePreferenceChange('performanceAlerts', e.target.checked)}
                    />
                  </div>

                  <div className="toggle-item">
                    <div className="toggle-info">
                      <div className="toggle-title">News Alerts</div>
                      <div className="toggle-desc">Market news related to your holdings</div>
                    </div>
                    <input
                      type="checkbox"
                      className="toggle-checkbox"
                      checked={preferences.newsAlerts}
                      onChange={(e) => handlePreferenceChange('newsAlerts', e.target.checked)}
                    />
                  </div>
                </div>
              </div>

              <div className="preferences-section">
                <h3>Report Settings</h3>
                <div className="form-group">
                  <label className="form-label">Daily Report</label>
                  <div className="checkbox-group">
                    <input
                      type="checkbox"
                      id="dailyReport"
                      checked={preferences.dailyReport}
                      onChange={(e) => handlePreferenceChange('dailyReport', e.target.checked)}
                    />
                    <label htmlFor="dailyReport" className="checkbox-label">Send daily portfolio report</label>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Report Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={preferences.reportTime}
                    onChange={(e) => handlePreferenceChange('reportTime', e.target.value)}
                  />
                </div>
              </div>

              <div className="preferences-section">
                <h3>Display Settings</h3>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="form-input"
                    value={preferences.currency}
                    onChange={(e) => handlePreferenceChange('currency', e.target.value)}
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                    <option value="SGD">SGD (S$)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Language</label>
                  <select
                    className="form-input"
                    value={preferences.language}
                    onChange={(e) => handlePreferenceChange('language', e.target.value)}
                  >
                    <option value="English">English</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="Mandarin">Mandarin</option>
                  </select>
                </div>

                <button className="btn btn-primary" onClick={handleSave}>
                  <FiSave /> Save Changes
                </button>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="tab-content card">
              <h2>Security Settings</h2>

              <div className="security-section">
                <h3>Two-Factor Authentication</h3>
                <div className="security-item">
                  <div className="security-info">
                    <div className="security-title">Secure Your Account</div>
                    <div className="security-desc">Add an extra layer of security to your account</div>
                  </div>
                  <button className="btn btn-secondary">
                    {security.twoFactorEnabled ? 'Disable' : 'Enable'} 2FA
                  </button>
                </div>
              </div>

              <div className="security-section">
                <h3>Login Activity</h3>
                <div className="toggle-item">
                  <div className="toggle-info">
                    <div className="toggle-title">Login Alerts</div>
                    <div className="toggle-desc">Get notified of new login attempts</div>
                  </div>
                  <input
                    type="checkbox"
                    className="toggle-checkbox"
                    checked={security.loginAlerts}
                    onChange={(e) => handleSecurityChange('loginAlerts', e.target.checked)}
                  />
                </div>
              </div>

              <div className="security-section">
                <h3>Session Management</h3>
                <div className="form-group">
                  <label className="form-label">Session Timeout (minutes)</label>
                  <select
                    className="form-input"
                    value={security.sessionTimeout}
                    onChange={(e) => handleSecurityChange('sessionTimeout', e.target.value)}
                  >
                    <option value="15">15 minutes</option>
                    <option value="30">30 minutes</option>
                    <option value="60">1 hour</option>
                    <option value="120">2 hours</option>
                  </select>
                </div>
              </div>

              <div className="security-section">
                <h3>Password</h3>
                <div className="password-info">
                  <p>Last changed: <strong>{security.lastPasswordChange}</strong></p>
                </div>
                <button className="btn btn-secondary">Change Password</button>
              </div>

              <button className="btn btn-primary" onClick={handleSave}>
                <FiSave /> Save Changes
              </button>
            </div>
          )}

          {/* Billing Tab */}
          {activeTab === 'billing' && (
            <div className="tab-content card">
              <h2>Billing Information</h2>
              <div className="billing-section">
                <div className="plan-card">
                  <div className="plan-name">Premium Plan</div>
                  <div className="plan-price">$9.99<span>/month</span></div>
                  <div className="plan-features">
                    <div className="feature">✓ Unlimited portfolios</div>
                    <div className="feature">✓ Advanced analytics</div>
                    <div className="feature">✓ AI recommendations</div>
                    <div className="feature">✓ Priority support</div>
                  </div>
                  <button className="btn btn-secondary">Manage Subscription</button>
                </div>
              </div>

              <div className="billing-section">
                <h3>Payment Methods</h3>
                <div className="payment-method">
                  <div className="payment-icon">💳</div>
                  <div className="payment-info">
                    <div className="payment-type">Visa ending in 4242</div>
                    <div className="payment-expiry">Expires 12/2025</div>
                  </div>
                  <button className="btn btn-sm btn-secondary">Edit</button>
                </div>
              </div>

              <div className="billing-section">
                <h3>Billing History</h3>
                <table className="billing-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>2024-01-01</td>
                      <td>Premium Plan - Monthly</td>
                      <td>$9.99</td>
                      <td><span className="badge badge-success">Paid</span></td>
                    </tr>
                    <tr>
                      <td>2023-12-01</td>
                      <td>Premium Plan - Monthly</td>
                      <td>$9.99</td>
                      <td><span className="badge badge-success">Paid</span></td>
                    </tr>
                    <tr>
                      <td>2023-11-01</td>
                      <td>Premium Plan - Monthly</td>
                      <td>$9.99</td>
                      <td><span className="badge badge-success">Paid</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;

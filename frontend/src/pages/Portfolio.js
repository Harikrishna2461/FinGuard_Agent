import React, { useState } from 'react';
import { FiPlus, FiEdit2, FiTrash2, FiSearch } from 'react-icons/fi';
import './Portfolio.css';

function Portfolio({ user }) {
  const [assets, setAssets] = useState([
    { id: 1, symbol: 'AAPL', name: 'Apple Inc.', quantity: 50, price: 189.50, value: 9475, sector: 'Technology', date: '2024-01-15' },
    { id: 2, symbol: 'MSFT', name: 'Microsoft Corp.', quantity: 30, price: 378.90, value: 11367, sector: 'Technology', date: '2024-02-20' },
    { id: 3, symbol: 'JNJ', name: 'Johnson & Johnson', quantity: 25, price: 158.40, value: 3960, sector: 'Healthcare', date: '2024-03-10' },
  ]);

  const [showForm, setShowForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({ symbol: '', name: '', quantity: '', price: '', sector: '' });

  const filteredAssets = assets.filter(asset =>
    asset.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddAsset = (e) => {
    e.preventDefault();
    const newAsset = {
      id: Date.now(),
      ...formData,
      quantity: parseFloat(formData.quantity),
      price: parseFloat(formData.price),
      value: parseFloat(formData.quantity) * parseFloat(formData.price),
      date: new Date().toISOString().split('T')[0]
    };
    setAssets([...assets, newAsset]);
    setFormData({ symbol: '', name: '', quantity: '', price: '', sector: '' });
    setShowForm(false);
  };

  const handleDeleteAsset = (id) => {
    setAssets(assets.filter(asset => asset.id !== id));
  };

  const totalValue = assets.reduce((sum, asset) => sum + asset.value, 0);

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <div>
          <h1>My Portfolio</h1>
          <p>Manage your investments and holdings</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          <FiPlus /> Add Asset
        </button>
      </div>

      {/* Portfolio Summary */}
      <div className="portfolio-summary card">
        <div className="summary-item">
          <div className="summary-label">Total Value</div>
          <div className="summary-value">${totalValue.toFixed(2)}</div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Total Assets</div>
          <div className="summary-value">{assets.length}</div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Largest Position</div>
          <div className="summary-value">
            {assets.length > 0 ? assets.reduce((max, asset) => asset.value > max.value ? asset : max).symbol : 'N/A'}
          </div>
        </div>
        <div className="summary-item">
          <div className="summary-label">Average Entry</div>
          <div className="summary-value">
            ${(assets.reduce((sum, asset) => sum + asset.price, 0) / assets.length).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Add Asset Form */}
      {showForm && (
        <div className="add-asset-form card">
          <h3>Add New Asset</h3>
          <form onSubmit={handleAddAsset}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Symbol</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., AAPL"
                  value={formData.symbol}
                  onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Company Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g., Apple Inc."
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Quantity</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0"
                  step="0.01"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Price per Share</label>
                <input
                  type="number"
                  className="form-input"
                  placeholder="0.00"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Sector</label>
                <select
                  className="form-input"
                  value={formData.sector}
                  onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
                  required
                >
                  <option value="">Select Sector</option>
                  <option value="Technology">Technology</option>
                  <option value="Healthcare">Healthcare</option>
                  <option value="Finance">Finance</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Consumer">Consumer</option>
                </select>
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary">Add Asset</button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Search and Filter */}
      <div className="search-bar">
        <FiSearch />
        <input
          type="text"
          placeholder="Search assets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Assets Table */}
      <div className="assets-table card">
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Company</th>
              <th>Sector</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Value</th>
              <th>Date Added</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAssets.map((asset) => (
              <tr key={asset.id}>
                <td><span className="symbol-badge">{asset.symbol}</span></td>
                <td>{asset.name}</td>
                <td><span className="sector-badge">{asset.sector}</span></td>
                <td>{asset.quantity}</td>
                <td>${asset.price.toFixed(2)}</td>
                <td className="value-cell">${asset.value.toFixed(2)}</td>
                <td>{asset.date}</td>
                <td className="actions-cell">
                  <button className="action-btn edit" title="Edit">
                    <FiEdit2 />
                  </button>
                  <button className="action-btn delete" onClick={() => handleDeleteAsset(asset.id)} title="Delete">
                    <FiTrash2 />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Portfolio;

import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  FiActivity,
  FiAlertTriangle,
  FiBarChart2,
  FiBell,
  FiBriefcase,
  FiCpu,
  FiDollarSign,
  FiFileText,
  FiHome,
  FiLogOut,
  FiMenu,
  FiSearch,
  FiShield,
  FiX
} from 'react-icons/fi';
import './Navbar.css';

function Navbar({ user }) {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: FiHome },
    { to: '/portfolio', label: 'Portfolios', icon: FiBriefcase },
    { to: '/analytics', label: 'Transaction Risk Analysis', icon: FiDollarSign },
    { to: '/', label: 'AI Analysis', icon: FiCpu },
    { to: '/alerts', label: 'Alerts', icon: FiBell },
    { to: '/search', label: 'Search', icon: FiSearch },
    { to: '/sentiment', label: 'Sentiment', icon: FiBarChart2 },
    { to: '/cases', label: 'Cases', icon: FiFileText }
  ];

  const agentChips = [
    'Alert Intake',
    'Customer Context',
    'Risk Assessment',
    'Risk Detection',
    'Explanation',
    'Escalation Summary',
    'Portfolio Analysis',
    'Market Intelligence',
    'Compliance'
  ];

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  return (
    <>
      <button className="sidebar-toggle" onClick={toggleMenu} aria-label="Toggle navigation">
        {isOpen ? <FiX /> : <FiMenu />}
      </button>
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <FiShield className="brand-icon" />
          <div>
            <div className="brand-name">FinGuard</div>
            <div className="run-status">RUNNING</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              onClick={() => setIsOpen(false)}
            >
              <Icon className="sidebar-icon" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="agent-count">9 INTERNAL AGENTS</div>
          <div className="agent-chip-grid">
            {agentChips.map((agent) => (
              <span key={agent} className="agent-chip">{agent}</span>
            ))}
          </div>
          <div className="sidebar-user">
            <span className="avatar">{user?.name?.charAt(0) || 'U'}</span>
            <span>{user?.name || 'User'}</span>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <FiLogOut />
            </button>
          </div>
          <div className="risk-strip">
            <FiActivity />
            <FiAlertTriangle />
            <span>Live monitoring</span>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Navbar;

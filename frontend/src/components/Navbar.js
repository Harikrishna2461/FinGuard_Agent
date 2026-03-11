import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiMenu, FiX, FiHome, FiTrendingUp, FiBarChart2, FiBell, FiSettings, FiLogOut } from 'react-icons/fi';
import { AiFillShield } from 'react-icons/ai';
import './Navbar.css';

function Navbar({ user }) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    window.location.href = '/';
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <AiFillShield className="logo-icon" />
          <span>FinGuard</span>
        </Link>

        {/* Menu Toggle */}
        <div className="menu-toggle" onClick={toggleMenu}>
          {isOpen ? <FiX /> : <FiMenu />}
        </div>

        {/* Navigation Menu */}
        <div className={`navbar-menu ${isOpen ? 'active' : ''}`}>
          <div className="nav-links">
            <Link to="/" className="nav-link">
              <FiHome /> Dashboard
            </Link>
            <Link to="/portfolio" className="nav-link">
              <FiTrendingUp /> Portfolio
            </Link>
            <Link to="/analytics" className="nav-link">
              <FiBarChart2 /> Analytics
            </Link>
            <Link to="/alerts" className="nav-link">
              <FiBell /> Alerts
            </Link>
          </div>

          {/* Right Side Menu */}
          <div className="navbar-right">
            <div className="user-info">
              <div className="avatar">{user?.name?.charAt(0) || 'U'}</div>
              <div className="user-details">
                <div className="user-name">{user?.name || 'User'}</div>
                <div className="user-email">{user?.email || 'user@finguard.com'}</div>
              </div>
            </div>
            <Link to="/settings" className="nav-link">
              <FiSettings /> Settings
            </Link>
            <button className="logout-btn" onClick={handleLogout}>
              <FiLogOut /> Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

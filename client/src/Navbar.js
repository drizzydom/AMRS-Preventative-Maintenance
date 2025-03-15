import React from 'react';
import { Link } from 'react-router-dom';
import './App.css';

function Navbar({ onLogout }) {
  const username = localStorage.getItem('username');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <Link className="navbar-brand" to="/">Maintenance Tracker</Link>
      <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span className="navbar-toggler-icon"></span>
      </button>
      <div className="collapse navbar-collapse" id="navbarNav">
        <ul className="navbar-nav mr-auto">
          <li className="nav-item">
            <Link className="nav-link" to="/">Home</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/add">Add Record</Link>
          </li>
          <li className="nav-item">
            <Link className="nav-link" to="/view">View Records</Link>
          </li>
          {isAdmin && (
            <li className="nav-item">
              <Link className="nav-link" to="/admin">Admin Panel</Link>
            </li>
          )}
        </ul>
        <ul className="navbar-nav">
          <li className="nav-item">
            <span className="nav-link text-light">Welcome, {username || 'User'}</span>
          </li>
          <li className="nav-item">
            <button onClick={onLogout} className="btn btn-outline-light my-2 my-sm-0">
              Logout
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;

import React from 'react';
import { Link } from 'react-router-dom';
import './App.css';

function Navbar() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <Link className="navbar-brand" to="/">Maintenance Tracker</Link>
      <div className="collapse navbar-collapse">
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
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;

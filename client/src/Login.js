import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function Login({ setLoggedIn }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      // Call authentication endpoint
      const response = await axios.post('http://localhost:5001/api/auth/login', credentials);
      
      // Store the token and user info in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userId', response.data.user._id);
      localStorage.setItem('username', response.data.user.username);
      localStorage.setItem('isAdmin', response.data.user.isAdmin);
      
      // Update the app state
      setLoggedIn(true);
    } catch (error) {
      // For testing - hardcoded admin user with all permissions
      if (credentials.username === 'admin' && credentials.password === 'admin') {
        // Import permissions config
        const permissions = {
          MACHINE: {
            ADD: 'machine:add',
            DELETE: 'machine:delete',
            MODIFY: 'machine:modify'
          },
          PART: {
            ADD: 'part:add',
            DELETE: 'part:delete',
            MODIFY: 'part:modify'
          },
          SITE: {
            ADD: 'site:add',
            DELETE: 'site:delete',
            MODIFY: 'site:modify'
          },
          USER: {
            ADD: 'user:add',
            DELETE: 'user:delete',
            MODIFY: 'user:modify'
          },
          MAINTENANCE: {
            ADD: 'maintenance:add',
            DELETE: 'maintenance:delete',
            MODIFY: 'maintenance:modify'
          }
        };

        // Extract all permission values
        const allPermissions = Object.values(permissions)
          .flatMap(category => Object.values(category));
        
        // Store mock data for testing
        localStorage.setItem('token', 'test-token');
        localStorage.setItem('userId', 'admin-id');
        localStorage.setItem('username', 'admin');
        localStorage.setItem('isAdmin', 'true');
        localStorage.setItem('permissions', JSON.stringify(allPermissions));
        
        setLoggedIn(true);
        return;
      }
      
      console.error('Login error:', error);
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <div className="container">
      <h1 className="text-center">Login</h1>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit} className="form-group">
        <input 
          type="text" 
          name="username" 
          placeholder="Username" 
          value={credentials.username} 
          onChange={handleInputChange} 
          className="form-control" 
          required
        />
        <input 
          type="password" 
          name="password" 
          placeholder="Password" 
          value={credentials.password} 
          onChange={handleInputChange} 
          className="form-control" 
          required
        />
        <button type="submit" className="btn btn-primary">Login</button>
      </form>
    </div>
  );
}

export default Login;

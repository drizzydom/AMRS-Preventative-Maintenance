import React, { useState } from 'react';
import './App.css';

function Login({ setLoggedIn }) {
  // State for form fields
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      console.log('Attempting login with:', { username, password });
      
      // Use plain fetch API instead of axios
      const response = await fetch('http://localhost:5001/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      
      // Get the response body as JSON
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }
      
      console.log('Login successful:', data);
      
      // Store authentication data in localStorage
      localStorage.setItem('token', data.token);
      localStorage.setItem('userId', data.user._id);
      localStorage.setItem('username', data.user.username);
      localStorage.setItem('isAdmin', data.user.isAdmin);
      
      // Store default permissions
      localStorage.setItem('permissions', JSON.stringify([
        'machine:add', 'machine:delete', 'machine:modify',
        'part:add', 'part:delete', 'part:modify',
        'site:add', 'site:delete', 'site:modify',
        'user:add', 'user:delete', 'user:modify'
      ]));
      
      // Update app state
      setLoggedIn(true);
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Login</h2>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>
          
          <button 
            type="submit" 
            disabled={loading}
            className="login-button"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div className="login-help">
          <p>Use username <strong>admin</strong> and password <strong>admin</strong></p>
        </div>
      </div>
    </div>
  );
}

export default Login;

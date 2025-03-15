import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function Login({ setLoggedIn }) {
  // Pre-fill with admin credentials for testing
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      // Log the login attempt
      console.log('Sending login request with:', { username, password });
      
      // Direct API call with minimal configuration
      const response = await axios.post('http://localhost:5001/login', { 
        username, 
        password 
      }, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      console.log('Login response:', response.data);
      
      // Save user data in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userId', response.data.user._id);
      localStorage.setItem('username', response.data.user.username);
      localStorage.setItem('isAdmin', 'true');
      
      // Add default permissions
      localStorage.setItem('permissions', JSON.stringify([
        'machine:add', 'machine:delete', 'machine:modify',
        'part:add', 'part:delete', 'part:modify',
        'site:add', 'site:delete', 'site:modify',
        'user:add', 'user:delete', 'user:modify'
      ]));
      
      // Update app state
      setLoggedIn(true);
    } catch (error) {
      console.error('Login error:', error);
      
      // Show a clear error message
      setError('Login failed. Please try again. Error: ' + 
        (error.response?.data?.message || error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header bg-primary text-white">
              <h2 className="mb-0 text-center">Login</h2>
            </div>
            <div className="card-body">
              {error && <div className="alert alert-danger">{error}</div>}
              
              <form onSubmit={handleSubmit}>
                <div className="form-group mb-3">
                  <label htmlFor="username">Username</label>
                  <input 
                    type="text" 
                    className="form-control" 
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
                
                <div className="form-group mb-3">
                  <label htmlFor="password">Password</label>
                  <input 
                    type="password" 
                    className="form-control" 
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
                
                <div className="d-grid gap-2">
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-block"
                    disabled={loading}
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </button>
                </div>
              </form>
              
              <div className="mt-3 text-center">
                <p><strong>Use these credentials:</strong> username: admin, password: admin</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;

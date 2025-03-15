import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function Login({ setLoggedIn }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      console.log('Attempting login with:', credentials.username);
      
      // Use the simplified login endpoint
      const response = await axios.post('http://localhost:5001/login', credentials);
      
      console.log('Login response:', response.data);
      
      // Store the token and user info in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userId', response.data.user._id);
      localStorage.setItem('username', response.data.user.username);
      localStorage.setItem('isAdmin', response.data.user.isAdmin);
      
      // Store admin permissions for this user
      const allPermissions = [
        'machine:add', 'machine:delete', 'machine:modify',
        'part:add', 'part:delete', 'part:modify',
        'site:add', 'site:delete', 'site:modify',
        'user:add', 'user:delete', 'user:modify',
        'maintenance:add', 'maintenance:delete', 'maintenance:modify'
      ];
      localStorage.setItem('permissions', JSON.stringify(allPermissions));
      
      // Update the app state
      setLoggedIn(true);
    } catch (error) {
      console.error('Login error:', error);
      setError('Invalid credentials or server error. Please try again.');
    } finally {
      setLoading(false);
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
          disabled={loading}
        />
        <input 
          type="password" 
          name="password" 
          placeholder="Password" 
          value={credentials.password} 
          onChange={handleInputChange} 
          className="form-control" 
          required
          disabled={loading}
        />
        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={loading}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <div className="mt-3 text-center">
        <p><strong>Admin Account:</strong> username: admin123, password: pass123</p>
      </div>
    </div>
  );
}

export default Login;

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
      // Call authentication endpoint
      const response = await axios.post('http://localhost:5001/api/auth/login', credentials);
      
      // Store the token and user info in localStorage
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('userId', response.data.user._id);
      localStorage.setItem('username', response.data.user.username);
      localStorage.setItem('isAdmin', response.data.user.isAdmin);
      
      // For testing - hardcode admin permissions
      if (credentials.username === 'cool') {
        const allPermissions = Object.values({
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
          }
        }).flatMap(category => Object.values(category));
        
        localStorage.setItem('permissions', JSON.stringify(allPermissions));
      } else {
        // Fetch permissions for the user
        try {
          const permissionsResponse = await axios.get('http://localhost:5001/api/permissions', {
            headers: {
              'Authorization': `Bearer ${response.data.token}`,
              'User-ID': response.data.user._id
            }
          });
          localStorage.setItem('permissions', JSON.stringify(permissionsResponse.data));
        } catch (permError) {
          console.error('Error fetching permissions:', permError);
          // Continue anyway with empty permissions
          localStorage.setItem('permissions', JSON.stringify([]));
        }
      }
      
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
        <p><strong>Admin Account:</strong> username: cool, password: cool</p>
      </div>
    </div>
  );
}

export default Login;

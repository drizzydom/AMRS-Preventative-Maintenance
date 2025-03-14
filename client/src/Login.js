import React, { useState } from 'react';
import './App.css';

function Login({ setLoggedIn }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Replace with actual authentication logic
    if (credentials.username === 'admin' && credentials.password === 'admin') {
      setLoggedIn(true);
    } else {
      alert('Invalid credentials');
    }
  };

  return (
    <div className="container">
      <h1 className="text-center">Login</h1>
      <form onSubmit={handleSubmit} className="form-group">
        <input type="text" name="username" placeholder="Username" value={credentials.username} onChange={handleInputChange} className="form-control" />
        <input type="password" name="password" placeholder="Password" value={credentials.password} onChange={handleInputChange} className="form-control" />
        <button type="submit" className="btn btn-primary">Login</button>
      </form>
    </div>
  );
}

export default Login;

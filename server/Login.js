import React, { useState } from 'react';

function Login({ setLoggedIn }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Replace with actual authentication logic
    if (credentials.username === 'admin' && credentials.password === 'password') {
      setLoggedIn(true);
    } else {
      alert('Invalid credentials');
    }
  };

  return (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="username" placeholder="Username" value={credentials.username} onChange={handleInputChange} />
        <input type="password" name="password" placeholder="Password" value={credentials.password} onChange={handleInputChange} />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;

const express = require('express');
const cors = require('cors');
const app = express();

// Enable CORS
app.use(cors());
app.use(express.json());

// Debug middleware to log all requests
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  console.log('Request body:', req.body);
  next();
});

// Simple login endpoint that always works
app.post('/login', (req, res) => {
  console.log('Login request received:', req.body);
  
  const { username, password } = req.body;
  
  // Accept any login with username "admin" and password "admin"
  if (username === 'admin' && password === 'admin') {
    console.log('Login successful');
    return res.json({
      success: true,
      token: 'fake-jwt-token',
      user: {
        _id: 'admin-user-id',
        username: 'admin',
        isAdmin: true
      }
    });
  }
  
  console.log('Login failed - invalid credentials');
  res.status(401).json({
    success: false,
    message: 'Invalid username or password'
  });
});

// Test route to verify server is running
app.get('/', (req, res) => {
  res.send('Server is running');
});

// Start server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log('Use username "admin" and password "admin" to log in');
  console.log(`Login endpoint: http://localhost:${PORT}/login`);
});

// Import bare minimum dependencies
const express = require('express');
const app = express();

// Configure CORS with a simple middleware
app.use((req, res, next) => {
  // Allow all origins
  res.header('Access-Control-Allow-Origin', '*');
  // Allow common headers
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  // Allow common methods
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  
  // Handle preflight OPTIONS requests
  if (req.method === 'OPTIONS') {
    console.log('Received OPTIONS request:', req.path);
    return res.status(200).end();
  }
  
  next();
});

// Basic request parsing
app.use(express.json());

// Debug logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  if (req.body && Object.keys(req.body).length > 0) {
    console.log('Request body:', req.body);
  }
  next();
});

// Server health check endpoint
app.get('/', (req, res) => {
  res.send('Server is running');
});

// Ultra simple login endpoint
app.post('/login', (req, res) => {
  console.log('Login request:', req.body);
  
  const { username, password } = req.body || {};
  
  // Accept admin/admin combination
  if (username === 'admin' && password === 'admin') {
    console.log('Login successful for admin');
    return res.json({
      success: true,
      token: 'admin-token-123456789',
      user: {
        _id: 'admin-id',
        username: 'admin',
        isAdmin: true
      }
    });
  }
  
  // Reject all other credentials
  console.log('Login failed for:', username);
  return res.status(401).json({
    success: false,
    message: 'Invalid username or password'
  });
});

// Mock data API endpoints
app.get('/api/sites', (req, res) => {
  res.json([
    { _id: '1', name: 'Main Factory' },
    { _id: '2', name: 'Warehouse B' }
  ]);
});

app.get('/api/machines', (req, res) => {
  res.json([
    { _id: '1', name: 'Machine 1' },
    { _id: '2', name: 'Machine 2' }
  ]);
});

app.get('/api/parts', (req, res) => {
  res.json([
    { _id: '1', name: 'Part 1' },
    { _id: '2', name: 'Part 2' }
  ]);
});

app.get('/api/users', (req, res) => {
  res.json([{ _id: '1', username: 'admin' }]);
});

app.get('/api/roles', (req, res) => {
  res.json([{ _id: '1', name: 'admin' }]);
});

app.get('/api/permissions', (req, res) => {
  res.json([
    'machine:add', 'machine:delete', 'machine:modify',
    'part:add', 'part:delete', 'part:modify',
    'site:add', 'site:delete', 'site:modify',
    'user:add', 'user:delete', 'user:modify'
  ]);
});

// Start server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log('Login endpoint: http://localhost:5001/login');
  console.log('Use admin/admin to log in');
});

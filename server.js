const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const User = require('./models/user');
const Role = require('./models/role');
const permissionsConfig = require('./config/permissions');
const app = express();

// Secret key for JWT
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Basic CORS settings - allow all origins for now
app.use(cors());

// Parse JSON requests
app.use(express.json());

// Routes that don't need auth middleware
app.post('/login', async (req, res) => {
  try {
    console.log('Login request received:', req.body);
    const { username, password } = req.body;
    
    // Find user by username
    const user = await User.findOne({ username }).populate('role');
    
    if (!user) {
      console.log('User not found:', username);
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    
    // Compare passwords
    const isMatch = await bcrypt.compare(password, user.password);
    
    if (!isMatch) {
      console.log('Password mismatch for user:', username);
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    
    // Create and sign JWT token
    const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '1d' });
    
    // Check if user is admin
    const isAdmin = await user.isAdmin();
    
    // Return user info without password
    const userResponse = {
      _id: user._id,
      username: user.username,
      role: user.role.name,
      isAdmin: isAdmin
    };
    
    console.log('Login successful for:', username);
    res.json({ token, user: userResponse });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Middleware for routes that need authentication
const authMiddleware = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  const userId = req.headers['user-id'];
  
  if (userId) {
    req.userId = userId;
  }
  
  if (token) {
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      req.userId = decoded.userId;
    } catch (err) {
      return res.status(401).json({ message: 'Invalid token' });
    }
  }
  
  next();
};

// Debug route
app.get('/', (req, res) => {
  res.send('Server is running!');
});

// Create fresh admin user
const resetAndCreateAdmin = async () => {
  try {
    console.log('Resetting database...');
    
    // Delete all users and roles
    await User.deleteMany({});
    await Role.deleteMany({});
    
    console.log('All users and roles deleted.');
    
    // Create admin role with all permissions
    const allPermissions = Object.values(permissionsConfig)
      .flatMap(category => Object.values(category));
    
    const adminRole = new Role({
      name: 'admin',
      isAdmin: true,
      permissions: allPermissions
    });
    
    await adminRole.save();
    console.log('Admin role created with all permissions');
    
    // Create admin user
    const username = 'admin123';
    const password = 'pass123';
    
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    const adminUser = new User({
      username,
      password: hashedPassword,
      role: adminRole._id
    });
    
    await adminUser.save();
    console.log(`Admin user created with username: ${username} and password: ${password}`);
  } catch (error) {
    console.error('Error resetting database:', error);
  }
};

// Connect to MongoDB and start server
const PORT = process.env.PORT || 5001;
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/preventative_maintenance', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(async () => {
  console.log('Connected to MongoDB');
  
  // Reset database and create admin user
  await resetAndCreateAdmin();
  
  // Start server after database setup
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log('Login with username: admin123 and password: pass123');
  });
})
.catch(err => console.error('MongoDB connection error:', err));

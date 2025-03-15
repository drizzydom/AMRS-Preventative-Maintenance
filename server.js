const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const routes = require('./routes/routes');
const User = require('./models/user');
const Role = require('./models/role');
const permissionsConfig = require('./config/permissions');
const app = express();

// Secret key for JWT
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// CORS configuration - configure correctly to handle preflight requests
app.use(cors({
    origin: 'http://localhost:3000', // React app URL
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'User-ID']
}));

app.use(express.json());

// Handle OPTIONS requests explicitly
app.options('*', cors());

// Authentication middleware - This handles token validation
app.use((req, res, next) => {
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
            // Token is invalid, but we'll continue anyway to allow subsequent auth checks
        }
    }
    next();
});

// Auth routes
app.post('/api/auth/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Find user by username
        const user = await User.findOne({ username }).populate('role');
        
        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Compare passwords
        const isMatch = await bcrypt.compare(password, user.password);
        
        if (!isMatch) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Create and sign JWT token
        const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '1d' });
        
        // Return user info without password and token
        const userResponse = {
            _id: user._id,
            username: user.username,
            role: user.role.name,
            isAdmin: await user.isAdmin()
        };
        
        res.json({ token, user: userResponse });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

// Create default admin user if it doesn't exist
const createDefaultAdmin = async () => {
    try {
        // Check if admin role exists
        let adminRole = await Role.findOne({ name: 'admin' });
        
        // Get all permissions from permissions config
        const allPermissions = Object.values(permissionsConfig)
            .flatMap(category => Object.values(category));
        
        // Create admin role if it doesn't exist
        if (!adminRole) {
            adminRole = new Role({
                name: 'admin',
                isAdmin: true,
                permissions: allPermissions
            });
            await adminRole.save();
            console.log('Admin role created with permissions:', allPermissions);
        } else {
            // Update admin role with all permissions if it exists
            adminRole.isAdmin = true;
            adminRole.permissions = allPermissions;
            await adminRole.save();
            console.log('Admin role updated with permissions:', allPermissions);
        }
        
        // Check if the cool admin user exists
        const adminExists = await User.findOne({ username: 'cool' });
        
        if (!adminExists) {
            // Hash password
            const salt = await bcrypt.genSalt(10);
            const hashedPassword = await bcrypt.hash('cool', salt);
            
            // Create new admin user
            const adminUser = new User({
                username: 'cool',
                password: hashedPassword,
                role: adminRole._id
            });
            
            await adminUser.save();
            console.log('New admin user created with username and password "cool"');
        }
    } catch (error) {
        console.error('Error creating default admin:', error);
    }
};

// Make auth endpoint accessible at root level as well for easier access
app.post('/auth/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Find user by username
        const user = await User.findOne({ username }).populate('role');
        
        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Compare passwords
        const isMatch = await bcrypt.compare(password, user.password);
        
        if (!isMatch) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Create and sign JWT token
        const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '1d' });
        
        // Return user info without password and token
        const userResponse = {
            _id: user._id,
            username: user.username,
            role: user.role.name,
            isAdmin: await user.isAdmin()
        };
        
        res.json({ token, user: userResponse });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

// API Routes
app.use('/api', routes);

// Debug route to check if server is responding
app.get('/', (req, res) => {
    res.json({ message: 'Server is running' });
});

// Serve static files from the React app in production
if (process.env.NODE_ENV === 'production') {
    const path = require('path');
    app.use(express.static('client/build'));
    app.get('*', (req, res) => {
        res.sendFile(path.resolve(__dirname, 'client', 'build', 'index.html'));
    });
}

// Connect to MongoDB
const mongoURI = process.env.MONGODB_URI || 'mongodb://localhost:27017/preventative_maintenance';
mongoose.connect(mongoURI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
.then(async () => {
    console.log('MongoDB connected');
    // Create default admin user
    await createDefaultAdmin();
})
.catch(err => console.log('MongoDB connection error:', err));

// Start server
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

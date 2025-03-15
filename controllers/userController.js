const permissions = require('../config/permissions');
const User = require('../models/user');
const Role = require('../models/role');
const bcrypt = require('bcryptjs');

exports.addUser = async (req, res) => {
    try {
        const requester = await User.findById(req.userId);
        // Allow creation if user has permission or is admin
        const hasPermission = await requester.hasPermission(permissions.USER.ADD) || await requester.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { username, password, roleId } = req.body;
        
        // Check if user already exists
        const existingUser = await User.findOne({ username });
        if (existingUser) {
            return res.status(400).send('User already exists');
        }
        
        // Hash password
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);
        
        const user = new User({
            username,
            password: hashedPassword,
            role: roleId
        });
        
        await user.save();
        
        // Don't return the password
        const userResponse = {
            id: user._id,
            username: user.username,
            role: user.role
        };
        
        return res.status(201).json(userResponse);
    } catch (error) {
        console.error('Error adding user:', error);
        return res.status(500).send('Server error');
    }
};

exports.deleteUser = async (req, res) => {
    try {
        const requester = await User.findById(req.userId);
        // Allow deletion if user has permission or is admin
        const hasPermission = await requester.hasPermission(permissions.USER.DELETE) || await requester.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const user = await User.findByIdAndDelete(req.params.id);
        if (!user) {
            return res.status(404).send('User not found');
        }
        
        return res.status(200).json({ message: 'User deleted' });
    } catch (error) {
        console.error('Error deleting user:', error);
        return res.status(500).send('Server error');
    }
};

exports.modifyUser = async (req, res) => {
    try {
        const requester = await User.findById(req.userId);
        // Allow modification if user has permission or is admin
        const hasPermission = await requester.hasPermission(permissions.USER.MODIFY) || await requester.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { username, password, roleId } = req.body;
        const user = await User.findById(req.params.id);
        if (!user) {
            return res.status(404).send('User not found');
        }
        
        if (username) user.username = username;
        if (password) {
            const salt = await bcrypt.genSalt(10);
            user.password = await bcrypt.hash(password, salt);
        }
        if (roleId) user.role = roleId;
        
        await user.save();
        
        // Don't return the password
        const userResponse = {
            id: user._id,
            username: user.username,
            role: user.role
        };
        
        return res.status(200).json(userResponse);
    } catch (error) {
        console.error('Error modifying user:', error);
        return res.status(500).send('Server error');
    }
};

exports.getAllUsers = async (req, res) => {
    try {
        const users = await User.find().select('-password').populate('role');
        return res.status(200).json(users);
    } catch (error) {
        console.error('Error getting users:', error);
        return res.status(500).send('Server error');
    }
};

exports.getUserById = async (req, res) => {
    try {
        const user = await User.findById(req.params.id).select('-password').populate('role');
        if (!user) {
            return res.status(404).send('User not found');
        }
        return res.status(200).json(user);
    } catch (error) {
        console.error('Error getting user:', error);
        return res.status(500).send('Server error');
    }
};

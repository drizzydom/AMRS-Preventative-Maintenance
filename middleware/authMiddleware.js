const User = require('../models/user');
const permissions = require('../config/permissions');

/**
 * Middleware to check if a user has a specific permission
 * @param {string} permission - The permission to check
 */
exports.checkPermission = (permission) => {
    return async (req, res, next) => {
        try {
            const user = await User.findById(req.userId);
            
            if (!user) {
                return res.status(401).json({ message: 'User not authenticated' });
            }

            // Check if user has permission or is admin
            const hasPermission = await user.hasPermission(permission) || await user.isAdmin();
            
            if (!hasPermission) {
                return res.status(403).json({ message: 'Permission denied' });
            }
            
            next();
        } catch (error) {
            console.error(`Permission check error: ${error}`);
            res.status(500).json({ message: 'Server error' });
        }
    };
};

/**
 * Middleware to check if a user is authenticated
 */
exports.isAuthenticated = async (req, res, next) => {
    try {
        if (!req.userId) {
            return res.status(401).json({ message: 'Authentication required' });
        }
        
        const user = await User.findById(req.userId);
        
        if (!user) {
            return res.status(401).json({ message: 'User not found' });
        }
        
        next();
    } catch (error) {
        console.error(`Authentication error: ${error}`);
        res.status(500).json({ message: 'Server error' });
    }
};

const permissions = require('../config/permissions');
const Site = require('../models/site');
const User = require('../models/user');

exports.addSite = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow creation if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.SITE.ADD) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name } = req.body;
        const site = new Site({ name });
        
        await site.save();
        return res.status(201).json(site);
    } catch (error) {
        console.error('Error adding site:', error);
        return res.status(500).send('Server error');
    }
};

exports.deleteSite = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow deletion if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.SITE.DELETE) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const site = await Site.findByIdAndDelete(req.params.id);
        if (!site) {
            return res.status(404).send('Site not found');
        }
        
        return res.status(200).json({ message: 'Site deleted' });
    } catch (error) {
        console.error('Error deleting site:', error);
        return res.status(500).send('Server error');
    }
};

exports.modifySite = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow modification if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.SITE.MODIFY) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name } = req.body;
        const site = await Site.findById(req.params.id);
        if (!site) {
            return res.status(404).send('Site not found');
        }
        
        site.name = name || site.name;
        
        await site.save();
        return res.status(200).json(site);
    } catch (error) {
        console.error('Error modifying site:', error);
        return res.status(500).send('Server error');
    }
};

exports.getAllSites = async (req, res) => {
    try {
        const sites = await Site.find();
        return res.status(200).json(sites);
    } catch (error) {
        console.error('Error getting sites:', error);
        return res.status(500).send('Server error');
    }
};

exports.getSiteById = async (req, res) => {
    try {
        const site = await Site.findById(req.params.id);
        if (!site) {
            return res.status(404).send('Site not found');
        }
        return res.status(200).json(site);
    } catch (error) {
        console.error('Error getting site:', error);
        return res.status(500).send('Server error');
    }
};

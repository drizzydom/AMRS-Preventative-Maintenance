const permissions = require('../config/permissions');
const Part = require('../models/part');
const User = require('../models/user');

exports.addPart = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow creation if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.PART.ADD) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name, machine_id } = req.body;
        const part = new Part({
            name,
            machine: machine_id
        });
        
        await part.save();
        return res.status(201).json(part);
    } catch (error) {
        console.error('Error adding part:', error);
        return res.status(500).send('Server error');
    }
};

exports.deletePart = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow deletion if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.PART.DELETE) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const part = await Part.findByIdAndDelete(req.params.id);
        if (!part) {
            return res.status(404).send('Part not found');
        }
        
        return res.status(200).json({ message: 'Part deleted' });
    } catch (error) {
        console.error('Error deleting part:', error);
        return res.status(500).send('Server error');
    }
};

exports.modifyPart = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow modification if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.PART.MODIFY) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name, machine_id } = req.body;
        const part = await Part.findById(req.params.id);
        if (!part) {
            return res.status(404).send('Part not found');
        }
        
        part.name = name || part.name;
        part.machine = machine_id || part.machine;
        
        await part.save();
        return res.status(200).json(part);
    } catch (error) {
        console.error('Error modifying part:', error);
        return res.status(500).send('Server error');
    }
};

exports.getAllParts = async (req, res) => {
    try {
        const parts = await Part.find().populate('machine');
        return res.status(200).json(parts);
    } catch (error) {
        console.error('Error getting parts:', error);
        return res.status(500).send('Server error');
    }
};

exports.getPartById = async (req, res) => {
    try {
        const part = await Part.findById(req.params.id).populate('machine');
        if (!part) {
            return res.status(404).send('Part not found');
        }
        return res.status(200).json(part);
    } catch (error) {
        console.error('Error getting part:', error);
        return res.status(500).send('Server error');
    }
};

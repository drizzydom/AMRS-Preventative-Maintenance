const permissions = require('../config/permissions');
const Maintenance = require('../models/maintenance');
const User = require('../models/user');

exports.addMaintenanceRecord = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow creation if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MAINTENANCE.ADD) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { machine, part, description, date } = req.body;
        const maintenanceRecord = new Maintenance({
            machine,
            part,
            description,
            date,
            createdBy: req.userId
        });
        
        await maintenanceRecord.save();
        return res.status(201).json(maintenanceRecord);
    } catch (error) {
        console.error('Error adding maintenance record:', error);
        return res.status(500).send('Server error');
    }
};

exports.deleteMaintenanceRecord = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow deletion if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MAINTENANCE.DELETE) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const maintenanceRecord = await Maintenance.findByIdAndDelete(req.params.id);
        if (!maintenanceRecord) {
            return res.status(404).send('Maintenance record not found');
        }
        
        return res.status(200).json({ message: 'Maintenance record deleted successfully' });
    } catch (error) {
        console.error('Error deleting maintenance record:', error);
        return res.status(500).send('Server error');
    }
};

exports.modifyMaintenanceRecord = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow modification if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MAINTENANCE.MODIFY) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { machine, part, description, date, completed } = req.body;
        const maintenanceRecord = await Maintenance.findById(req.params.id);
        if (!maintenanceRecord) {
            return res.status(404).send('Maintenance record not found');
        }
        
        if (machine) maintenanceRecord.machine = machine;
        if (part) maintenanceRecord.part = part;
        if (description) maintenanceRecord.description = description;
        if (date) maintenanceRecord.date = date;
        if (completed !== undefined) maintenanceRecord.completed = completed;
        
        maintenanceRecord.updatedBy = req.userId;
        maintenanceRecord.updatedAt = Date.now();
        
        await maintenanceRecord.save();
        return res.status(200).json(maintenanceRecord);
    } catch (error) {
        console.error('Error modifying maintenance record:', error);
        return res.status(500).send('Server error');
    }
};

exports.getAllMaintenanceRecords = async (req, res) => {
    try {
        const maintenanceRecords = await Maintenance.find()
            .populate('machine')
            .populate('part')
            .populate('createdBy', 'username')
            .populate('updatedBy', 'username');
            
        return res.status(200).json(maintenanceRecords);
    } catch (error) {
        console.error('Error getting maintenance records:', error);
        return res.status(500).send('Server error');
    }
};

exports.getMaintenanceRecordById = async (req, res) => {
    try {
        const maintenanceRecord = await Maintenance.findById(req.params.id)
            .populate('machine')
            .populate('part')
            .populate('createdBy', 'username')
            .populate('updatedBy', 'username');
            
        if (!maintenanceRecord) {
            return res.status(404).send('Maintenance record not found');
        }
        
        return res.status(200).json(maintenanceRecord);
    } catch (error) {
        console.error('Error getting maintenance record:', error);
        return res.status(500).send('Server error');
    }
};

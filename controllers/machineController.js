const permissions = require('../config/permissions');
const Machine = require('../models/machine');
const User = require('../models/user');

exports.addMachine = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow creation if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MACHINE.ADD) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name, site_id } = req.body;
        const machine = new Machine({
            name,
            site: site_id
        });
        
        await machine.save();
        return res.status(201).json(machine);
    } catch (error) {
        console.error('Error adding machine:', error);
        return res.status(500).send('Server error');
    }
};

exports.deleteMachine = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow deletion if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MACHINE.DELETE) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const machine = await Machine.findByIdAndDelete(req.params.id);
        if (!machine) {
            return res.status(404).send('Machine not found');
        }
        
        return res.status(200).json({ message: 'Machine deleted successfully' });
    } catch (error) {
        console.error('Error deleting machine:', error);
        return res.status(500).send('Server error');
    }
};

exports.modifyMachine = async (req, res) => {
    try {
        const user = await User.findById(req.userId);
        // Allow modification if user has permission or is admin
        const hasPermission = await user.hasPermission(permissions.MACHINE.MODIFY) || await user.isAdmin();
        if (!hasPermission) {
            return res.status(403).send('Permission denied');
        }
        
        const { name, site_id } = req.body;
        const machine = await Machine.findById(req.params.id);
        if (!machine) {
            return res.status(404).send('Machine not found');
        }
        
        if (name) machine.name = name;
        if (site_id) machine.site = site_id;
        
        await machine.save();
        return res.status(200).json(machine);
    } catch (error) {
        console.error('Error modifying machine:', error);
        return res.status(500).send('Server error');
    }
};

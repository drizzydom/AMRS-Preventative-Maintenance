const Machine = require('../models/machine');

exports.addMachine = async (req, res) => {
    try {
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

exports.getAllMachines = async (req, res) => {
    try {
        const machines = await Machine.find().populate('site', 'name');
        return res.status(200).json(machines);
    } catch (error) {
        console.error('Error getting machines:', error);
        return res.status(500).send('Server error');
    }
};

exports.getMachineById = async (req, res) => {
    try {
        const machine = await Machine.findById(req.params.id).populate('site', 'name');
        if (!machine) {
            return res.status(404).send('Machine not found');
        }
        return res.status(200).json(machine);
    } catch (error) {
        console.error('Error getting machine:', error);
        return res.status(500).send('Server error');
    }
};

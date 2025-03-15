const permissions = require('../config/permissions');
const Machine = require('../models/machine');
const User = require('../models/user');

exports.addMachine = async (req, res) => {
    const user = await User.findById(req.userId);
    if (!await user.hasPermission(permissions.MACHINE.ADD)) {
        return res.status(403).send('Permission denied');
    }
    if (!user.isAdmin) {
        return res.status(403).send('Admin permission required');
    }
    // ...existing code...
};

exports.deleteMachine = async (req, res) => {
    const user = await User.findById(req.userId);
    if (!await user.hasPermission(permissions.MACHINE.DELETE)) {
        return res.status(403).send('Permission denied');
    }
    if (!user.isAdmin) {
        return res.status(403).send('Admin permission required');
    }
    // ...existing code...
};

exports.modifyMachine = async (req, res) => {
    const user = await User.findById(req.userId);
    if (!await user.hasPermission(permissions.MACHINE.MODIFY)) {
        return res.status(403).send('Permission denied');
    }
    if (!user.isAdmin) {
        return res.status(403).send('Admin permission required');
    }
    // ...existing code...
};

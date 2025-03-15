const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const MaintenanceSchema = new Schema({
    machine: {
        type: Schema.Types.ObjectId,
        ref: 'Machine',
        required: true
    },
    part: {
        type: Schema.Types.ObjectId,
        ref: 'Part',
        required: true
    },
    description: {
        type: String,
        required: true
    },
    date: {
        type: Date,
        required: true
    },
    completed: {
        type: Boolean,
        default: false
    },
    createdBy: {
        type: Schema.Types.ObjectId,
        ref: 'User'
    },
    updatedBy: {
        type: Schema.Types.ObjectId,
        ref: 'User'
    },
    createdAt: {
        type: Date,
        default: Date.now
    },
    updatedAt: {
        type: Date
    }
});

module.exports = mongoose.model('Maintenance', MaintenanceSchema);

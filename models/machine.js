const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const MachineSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    site: {
        type: Schema.Types.ObjectId,
        ref: 'Site',
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Machine', MachineSchema);

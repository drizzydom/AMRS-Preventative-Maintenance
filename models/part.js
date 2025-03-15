const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const PartSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    machine: {
        type: Schema.Types.ObjectId,
        ref: 'Machine',
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Part', PartSchema);

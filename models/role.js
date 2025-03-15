const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const RoleSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    permissions: {
        type: [String],
        default: []
    },
    isAdmin: {
        type: Boolean,
        default: false
    }
});

module.exports = mongoose.model('Role', RoleSchema);

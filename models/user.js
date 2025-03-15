const mongoose = require('mongoose');
const Schema = mongoose.Schema;
const Role = require('./role');

const UserSchema = new Schema({
    username: {
        type: String,
        required: true
    },
    password: {
        type: String,
        required: true
    },
    role: {
        type: Schema.Types.ObjectId,
        ref: 'Role'
    }
});

UserSchema.methods.hasPermission = async function(permission) {
    const role = await Role.findById(this.role);
    if (!role) return false;
    return role.permissions.includes(permission);
};

UserSchema.methods.isAdmin = async function() {
    const role = await Role.findById(this.role);
    if (!role) return false;
    return role.isAdmin === true || role.name === 'admin';
};

module.exports = mongoose.model('User', UserSchema);

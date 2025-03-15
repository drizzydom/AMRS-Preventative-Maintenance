const permissions = {
    MACHINE: {
        ADD: 'machine:add',
        DELETE: 'machine:delete',
        MODIFY: 'machine:modify'
    },
    PART: {
        ADD: 'part:add',
        DELETE: 'part:delete',
        MODIFY: 'part:modify'
    },
    SITE: {
        ADD: 'site:add',
        DELETE: 'site:delete',
        MODIFY: 'site:modify'
    },
    USER: {
        ADD: 'user:add',
        DELETE: 'user:delete',
        MODIFY: 'user:modify'
    },
    MAINTENANCE: {
        ADD: 'maintenance:add',
        DELETE: 'maintenance:delete',
        MODIFY: 'maintenance:modify'
    }
};

module.exports = permissions;

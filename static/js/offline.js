// This file will store functions to check network connectivity and sync status
function checkConnection() {
    return fetch('/api/check-connection', {
        method: 'GET',
        cache: 'no-cache',
    })
    .then(response => response.json())
    .then(data => {
        return data.online;
    })
    .catch(() => {
        return false;
    });
}

function updateConnectionStatus() {
    checkConnection().then(isOnline => {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.className = isOnline ? 'status-online' : 'status-offline';
            statusEl.innerText = isOnline ? 'Online' : 'Offline';
        }
    });
}

function getSyncStatus() {
    return fetch('/api/sync/status', {
        method: 'GET',
        cache: 'no-cache',
    })
    .then(response => response.json())
    .catch(() => {
        return { 
            last_sync: null, 
            pending_changes: 0,
            sync_in_progress: false 
        };
    });
}

function updateSyncStatus() {
    getSyncStatus().then(status => {
        const syncEl = document.getElementById('sync-status');
        const syncTimeEl = document.getElementById('last-sync-time');
        const pendingChangesEl = document.getElementById('pending-changes');
        
        if (syncEl) {
            if (status.sync_in_progress) {
                syncEl.className = 'sync-in-progress';
                syncEl.innerText = 'Syncing...';
            } else if (status.pending_changes > 0) {
                syncEl.className = 'sync-pending';
                syncEl.innerText = 'Sync Needed';
            } else {
                syncEl.className = 'sync-ok';
                syncEl.innerText = 'Synced';
            }
        }
        
        if (syncTimeEl && status.last_sync) {
            const syncDate = new Date(status.last_sync);
            syncTimeEl.innerText = syncDate.toLocaleString();
        }
        
        if (pendingChangesEl) {
            pendingChangesEl.innerText = status.pending_changes > 0 ? 
                `${status.pending_changes} pending change(s)` : 'No pending changes';
        }
    });
}

function triggerManualSync() {
    const syncButton = document.getElementById('manual-sync-button');
    if (syncButton) {
        syncButton.disabled = true;
        syncButton.innerText = 'Syncing...';
    }
    
    return fetch('/api/sync/manual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (syncButton) {
            syncButton.disabled = false;
            syncButton.innerText = 'Sync Now';
        }
        
        if (data.success) {
            showNotification('Sync completed successfully', 'success');
        } else {
            showNotification('Sync failed: ' + data.message, 'error');
        }
        
        updateSyncStatus();
        return data;
    })
    .catch(error => {
        if (syncButton) {
            syncButton.disabled = false;
            syncButton.innerText = 'Sync Now';
        }
        showNotification('Sync failed: Network error', 'error');
        console.error('Sync error:', error);
        updateSyncStatus();
        return { success: false, message: 'Network error' };
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerText = message;
    
    const container = document.getElementById('notification-container') || document.body;
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('notification-fade-out');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 3000);
}

// Initialize status updates when document is ready
document.addEventListener('DOMContentLoaded', () => {
    updateConnectionStatus();
    updateSyncStatus();
    
    // Set up interval to periodically check status
    setInterval(updateConnectionStatus, 30000); // Every 30 seconds
    setInterval(updateSyncStatus, 60000); // Every minute
    
    // Add event listener to manual sync button if it exists
    const syncButton = document.getElementById('manual-sync-button');
    if (syncButton) {
        syncButton.addEventListener('click', triggerManualSync);
    }
});

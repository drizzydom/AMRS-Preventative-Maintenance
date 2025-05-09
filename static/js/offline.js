// This file handles functions to check network connectivity and sync status
let isOnline = true;
let offlineMode = false;
let syncInProgress = false;

function checkConnection() {
    return fetch('/api/connection/status', {
        method: 'GET',
        cache: 'no-cache',
    })
    .then(response => response.json())
    .then(data => {
        isOnline = data.status === 'connected';
        offlineMode = data.offline_mode === true;
        return isOnline;
    })
    .catch(() => {
        isOnline = false;
        return false;
    });
}

function updateConnectionStatus() {
    checkConnection().then(isConnected => {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.className = isConnected ? 'status-online' : 'status-offline';
            statusEl.innerText = isConnected ? (offlineMode ? 'Offline Mode' : 'Online') : 'Offline';
        }
        
        // Show or hide offline banner
        if (!isConnected || offlineMode) {
            showOfflineBanner();
        } else {
            hideOfflineBanner();
        }
    });
}

function showOfflineBanner() {
    // Only show if it doesn't already exist
    if (document.getElementById('offline-banner')) return;
    
    const banner = document.createElement('div');
    banner.id = 'offline-banner';
    banner.className = 'alert alert-warning alert-dismissible fade show m-0';
    banner.style.borderRadius = '0';
    banner.innerHTML = `
        <div class="container">
            <strong>Offline Mode Active</strong> - You are working with a local database. 
            Changes will be synced when you reconnect.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Insert at the top of the page, after the navbar if it exists
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.parentNode.insertBefore(banner, navbar.nextSibling);
    } else {
        document.body.insertBefore(banner, document.body.firstChild);
    }
}

function hideOfflineBanner() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
        banner.remove();
    }
}

function getSyncStatus() {
    return fetch('/api/sync/status', {
        method: 'GET',
        cache: 'no-cache',
    })
    .then(response => response.json())
    .then(data => {
        return { 
            last_sync: data.last_sync, 
            pending_changes: data.pending_sync ? data.pending_sync.total : 0,
            sync_in_progress: syncInProgress 
        };
    })
    .catch(() => {
        return { 
            last_sync: null, 
            pending_changes: 0,
            sync_in_progress: syncInProgress 
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
    
    syncInProgress = true;
    updateSyncStatus();
    
    return fetch('/api/sync/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        syncInProgress = false;
        
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
        syncInProgress = false;
        
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
    
    // Add online/offline event listeners
    window.addEventListener('online', () => {
        isOnline = true;
        updateConnectionStatus();
        if (!syncInProgress) {
            triggerManualSync(); // Auto-sync when connection is restored
        }
    });
    
    window.addEventListener('offline', () => {
        isOnline = false;
        updateConnectionStatus();
    });
});

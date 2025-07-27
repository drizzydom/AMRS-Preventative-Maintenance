// static/js/socket-sync.js
// Memory-optimized Client-side Socket.IO for real-time sync

// Make sure to include socket.io client in your HTML:
// <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
// <script src="/static/js/socket-sync.js"></script>

(function() {
    let socket = null;
    let reconnectAttempts = 0;
    let maxReconnectAttempts = 5;
    let reconnectDelay = 1000; // Start with 1 second
    let heartbeatInterval = null;
    let connectionTimeout = null;
    let isManualDisconnect = false;

    // Connection configuration for offline client stability
    const socketConfig = {
        transports: ['polling', 'websocket'], // Start with polling, upgrade to websocket
        upgrade: true,
        rememberUpgrade: false, // Don't remember websocket upgrade to avoid issues
        timeout: 30000, // Increased timeout for slower connections
        forceNew: true, // Prevent connection reuse issues
        autoConnect: false, // Manual connection control
        reconnection: false, // Handle reconnection manually
        pingTimeout: 120000, // Match server ping timeout
        pingInterval: 60000,  // Match server ping interval
        maxHttpBufferSize: 1e6 // 1MB buffer
    };

    function connectSocket() {
        // Prevent multiple connections
        if (socket && socket.connected) {
            console.log('[SocketIO] Already connected, skipping...');
            return;
        }

        // Clean up existing socket if present
        if (socket) {
            socket.disconnect();
            socket = null;
        }

        try {
            console.log('[SocketIO] Attempting to connect...');
            socket = io(window.location.origin, socketConfig);

            // Connection successful
            socket.on('connect', function() {
                console.log('[SocketIO] Connected successfully');
                reconnectAttempts = 0;
                reconnectDelay = 1000;
                isManualDisconnect = false;
                
                // Start heartbeat to maintain connection health
                startHeartbeat();
                
                // Clear connection timeout
                if (connectionTimeout) {
                    clearTimeout(connectionTimeout);
                    connectionTimeout = null;
                }
            });

            // Handle server confirmation
            socket.on('connected', function(data) {
                console.log('[SocketIO] Server confirmed connection:', data.client_id || 'unknown');
            });

            // Handle sync events
            socket.on('sync', function(data) {
                console.log('[SocketIO] Sync event received:', data.message);
                
                // Trigger your incremental sync logic here
                if (window.performIncrementalSync) {
                    window.performIncrementalSync();
                } else {
                    // Fallback: reload the page to get fresh data
                    window.location.reload();
                }
            });

            // Handle heartbeat responses
            socket.on('heartbeat', function(data) {
                // Silent heartbeat response - server is checking if we're alive
                console.log('[SocketIO] Heartbeat received from server');
            });

            socket.on('pong', function(data) {
                // Response to our ping
                console.log('[SocketIO] Pong received from server');
            });

            // Connection failed
            socket.on('connect_error', function(error) {
                console.error('[SocketIO] Connection failed:', error.message || error);
                console.error('[SocketIO] Error details:', error);
                if (!isManualDisconnect) {
                    handleReconnect();
                }
            });

            // Handle transport errors specifically
            socket.on('error', function(error) {
                console.error('[SocketIO] Transport error:', error);
            });

            // Disconnection handling
            socket.on('disconnect', function(reason) {
                console.log('[SocketIO] Disconnected:', reason);
                stopHeartbeat();
                
                if (isManualDisconnect) {
                    console.log('[SocketIO] Manual disconnect, not reconnecting');
                    return;
                }
                
                // Only attempt reconnect for certain disconnect reasons
                if (reason === 'io server disconnect') {
                    // Server-initiated disconnect, don't reconnect automatically
                    console.log('[SocketIO] Server disconnected us, not reconnecting');
                } else {
                    // Network issues or client-side disconnect, attempt reconnect
                    handleReconnect();
                }
            });

            // Set connection timeout
            connectionTimeout = setTimeout(() => {
                if (!socket.connected) {
                    console.log('[SocketIO] Connection timeout');
                    socket.disconnect();
                    if (!isManualDisconnect) {
                        handleReconnect();
                    }
                }
            }, 10000);

            // Initiate connection
            socket.connect();

        } catch (error) {
            console.error('[SocketIO] Failed to create socket:', error);
            if (!isManualDisconnect) {
                handleReconnect();
            }
        }
    }

    function handleReconnect() {
        if (isManualDisconnect || reconnectAttempts >= maxReconnectAttempts) {
            console.log('[SocketIO] Max reconnection attempts reached or manual disconnect, giving up');
            return;
        }

        reconnectAttempts++;
        const delay = Math.min(reconnectDelay * Math.pow(2, reconnectAttempts - 1), 30000); // Max 30 seconds
        
        console.log(`[SocketIO] Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
        
        setTimeout(() => {
            if (!isManualDisconnect) {
                connectSocket();
            }
        }, delay);
    }

    function startHeartbeat() {
        stopHeartbeat(); // Clear existing interval
        
        // Send periodic ping to maintain connection
        heartbeatInterval = setInterval(() => {
            if (socket && socket.connected) {
                socket.emit('ping');
            } else {
                stopHeartbeat();
            }
        }, 25000); // Every 25 seconds
    }

    function stopHeartbeat() {
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
        }
    }

    function disconnectSocket() {
        console.log('[SocketIO] Manually disconnecting...');
        isManualDisconnect = true;
        stopHeartbeat();
        
        if (connectionTimeout) {
            clearTimeout(connectionTimeout);
            connectionTimeout = null;
        }
        
        if (socket) {
            socket.disconnect();
            socket = null;
        }
        
        reconnectAttempts = maxReconnectAttempts; // Prevent auto-reconnect
    }

    // Page lifecycle management
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[SocketIO] DOM loaded, initializing connection...');
        connectSocket();
    });

    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        disconnectSocket();
    });

    // Handle page visibility changes (mobile apps, tab switching)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            // Page hidden, reduce activity
            stopHeartbeat();
        } else {
            // Page visible, resume activity
            if (socket && socket.connected) {
                startHeartbeat();
            } else if (!isManualDisconnect) {
                // Reconnect if needed
                reconnectAttempts = 0; // Reset attempts when page becomes visible
                connectSocket();
            }
        }
    });

    // Expose socket for debugging and compatibility
    window.amrsSocket = socket; // Will be updated when socket is created
    
    // Expose control functions
    window.amrsSocketControl = {
        connect: connectSocket,
        disconnect: disconnectSocket,
        isConnected: () => socket && socket.connected,
        getSocket: () => socket,
        resetConnection: () => {
            isManualDisconnect = false;
            reconnectAttempts = 0;
            connectSocket();
        }
    };
})();

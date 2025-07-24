// static/js/socket-sync.js
// Client-side Socket.IO for real-time sync

// Make sure to include socket.io client in your HTML:
// <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
// <script src="/static/js/socket-sync.js"></script>

(function() {
    // Connect to the server's Socket.IO endpoint
    // Use window.location.origin to match the current host/port
    const socket = io(window.location.origin, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 2000
    });

    socket.on('connect', function() {
        console.log('[SocketIO] Connected to sync server');
    });

    socket.on('connected', function(data) {
        console.log('[SocketIO] Server says:', data.message);
    });

    socket.on('sync', function(data) {
        console.log('[SocketIO] Sync event received:', data.message);
        // Trigger your incremental sync logic here
        // For example, reload data via AJAX or refresh the page
        if (window.performIncrementalSync) {
            window.performIncrementalSync();
        } else {
            // Fallback: reload the page to get fresh data
            window.location.reload();
        }
    });

    socket.on('disconnect', function() {
        console.warn('[SocketIO] Disconnected from sync server');
    });

    // Expose socket for debugging
    window.amrsSocket = socket;
})();

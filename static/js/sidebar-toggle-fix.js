/**
 * SIDEBAR TOGGLE FUNCTIONALITY FIX
 * Simple, reliable toggle for sidebar expansion/collapse
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find the toggle button - try multiple selectors to ensure we find it
    const toggleButtons = document.querySelectorAll('.sidebar-toggle-btn, .sidebar-toggle');
    
    // Add click handler to all potential toggle buttons
    toggleButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            toggleSidebar();
        });
    });
    
    // Also look for any elements with onclick="toggleSidebar()"
    document.querySelectorAll('[onclick*="toggleSidebar"]').forEach(function(element) {
        // Make sure onclick actually works by setting it programmatically too
        element.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    });
    
    // Define the toggle function in global scope so it's accessible from HTML onclick
    window.toggleSidebar = function() {
        document.body.classList.toggle('sidebar-collapsed');
        
        // Store the state in localStorage
        if (document.body.classList.contains('sidebar-collapsed')) {
            localStorage.setItem('sidebar-collapsed', 'true');
        } else {
            localStorage.removeItem('sidebar-collapsed');
        }
        
        // Fire an event that signals the sidebar state changed (for other scripts)
        const event = new CustomEvent('sidebarToggled', { 
            detail: { collapsed: document.body.classList.contains('sidebar-collapsed') } 
        });
        document.dispatchEvent(event);
    };
    
    // Load saved state on page load
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        document.body.classList.add('sidebar-collapsed');
    }
    
    // Add the hamburger icon to the sidebar if it doesn't exist
    if (document.querySelectorAll('.sidebar-toggle-item, .sidebar-toggle-btn').length === 0) {
        const sidebar = document.querySelector('.sidebar, .sidebar-nav');
        if (sidebar) {
            const toggleItem = document.createElement('li');
            toggleItem.className = 'sidebar-toggle-item';
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'sidebar-toggle-btn';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            toggleBtn.addEventListener('click', toggleSidebar);
            
            toggleItem.appendChild(toggleBtn);
            sidebar.insertBefore(toggleItem, sidebar.firstChild);
        }
    }
});

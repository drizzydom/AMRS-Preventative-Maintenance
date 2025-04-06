/**
 * SIDEBAR HAMBURGER BUTTON FIX
 * Ensures the hamburger button properly toggles the sidebar on mobile devices
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get relevant elements
    const hamburgerToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;
    
    // Ensure elements exist
    if (!hamburgerToggle || !sidebar) {
        console.error('Sidebar toggle elements not found');
        return;
    }
    
    // Add click handler to hamburger button
    hamburgerToggle.addEventListener('click', function(event) {
        console.log('Hamburger clicked');
        
        // Prevent default behavior and stop propagation
        event.preventDefault();
        event.stopPropagation();
        
        // Toggle sidebar visibility
        sidebar.classList.toggle('show');
        body.classList.toggle('sidebar-active');
        
        // Update ARIA attributes
        const isExpanded = sidebar.classList.contains('show');
        hamburgerToggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        if (window.innerWidth > 991.98) return; // Only on mobile
        
        const isInsideSidebar = sidebar.contains(event.target);
        const isToggleButton = hamburgerToggle.contains(event.target);
        
        // If click is outside sidebar and toggle button, and sidebar is shown
        if (!isInsideSidebar && !isToggleButton && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
            hamburgerToggle.setAttribute('aria-expanded', 'false');
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
            hamburgerToggle.setAttribute('aria-expanded', 'false');
        }
    });
});

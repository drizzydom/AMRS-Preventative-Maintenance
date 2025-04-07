/**
 * ULTRA SIMPLE HAMBURGER BUTTON HANDLER
 * This script directly attaches an event listener to the hamburger button
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Simple hamburger script loaded");
    
    // Get the hamburger button and sidebar elements
    const hamburgerButton = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    
    // Log for debugging
    console.log("Hamburger button:", hamburgerButton);
    console.log("Sidebar:", sidebar);
    
    // Only proceed if both elements exist
    if (!hamburgerButton || !sidebar) {
        console.error("Could not find hamburger button or sidebar");
        return;
    }
    
    // Add click handler to hamburger button
    hamburgerButton.addEventListener('click', function(e) {
        // Prevent default behavior and bubbling
        e.preventDefault();
        e.stopPropagation();
        
        console.log("Hamburger button clicked");
        
        // Toggle the 'show' class on the sidebar
        sidebar.classList.toggle('show');
        
        // Toggle body class for overlay effect
        document.body.classList.toggle('sidebar-active');
        
        console.log("Sidebar visibility toggled:", sidebar.classList.contains('show'));
    });
    
    // Add click handler to close sidebar when clicking outside
    document.addEventListener('click', function(e) {
        // If sidebar is visible and click is outside sidebar and hamburger button
        if (sidebar.classList.contains('show') && 
            !sidebar.contains(e.target) && 
            !hamburgerButton.contains(e.target)) {
            
            console.log("Closing sidebar - clicked outside");
            sidebar.classList.remove('show');
            document.body.classList.remove('sidebar-active');
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            console.log("Closing sidebar - Escape key");
            sidebar.classList.remove('show');
            document.body.classList.remove('sidebar-active');
        }
    });
});

/**
 * Emergency hamburger button fix
 * This script completely replaces any existing hamburger functionality
 */
(function() {
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log("Emergency hamburger fix loading");
    
    // Get references to the key elements
    const hamburger = document.getElementById('hamburger-btn');
    const sidebar = document.querySelector('.sidebar');
    
    // Exit if elements don't exist
    if (!hamburger || !sidebar) {
      console.error("Required elements not found!");
      return;
    }
    
    console.log("Found required elements, setting up handlers");
    
    // Remove any existing event listeners by cloning
    const newHamburger = hamburger.cloneNode(true);
    hamburger.parentNode.replaceChild(newHamburger, hamburger);
    
    // Add our custom click handler
    newHamburger.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log("Hamburger button clicked");
      
      // Toggle sidebar visibility
      if (sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
      } else {
        sidebar.classList.add('show');
        document.body.classList.add('sidebar-active');
      }
    });
    
    // Add a click handler to the document to close sidebar when clicking outside
    document.addEventListener('click', function(e) {
      // Only proceed if sidebar is showing
      if (!sidebar.classList.contains('show')) return;
      
      // Check if click is outside sidebar and hamburger
      if (!sidebar.contains(e.target) && 
          e.target !== newHamburger && 
          !newHamburger.contains(e.target)) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
      }
    });
    
    // Add specific class for parts page
    if (window.location.pathname.includes('/parts')) {
      document.body.classList.add('parts-page');
      console.log("Added parts-page class to body");
    }
    
    console.log("Emergency hamburger fix initialized");
  });
})();

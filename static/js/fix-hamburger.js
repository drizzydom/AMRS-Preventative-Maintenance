/**
 * EMERGENCY FIX FOR HAMBURGER BUTTON
 * This script directly fixes the hamburger button functionality
 * by attaching a simple click handler that toggles the sidebar
 */

// IIFE for immediate execution and variable isolation
(function() {
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('Hamburger fix loaded');
    
    // Get direct references to the hamburger button and sidebar
    var hamburgerButton = document.querySelector('.navbar-toggler');
    var sidebar = document.querySelector('.sidebar');
    
    if (!hamburgerButton || !sidebar) {
      console.error('Cannot find hamburger button or sidebar elements');
      return;
    }
    
    // Remove any existing click event listeners from the hamburger button
    var newHamburgerButton = hamburgerButton.cloneNode(true);
    hamburgerButton.parentNode.replaceChild(newHamburgerButton, hamburgerButton);
    
    // Add our own direct click handler to the cloned button
    newHamburgerButton.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Hamburger button clicked');
      
      // Toggle sidebar visibility class
      sidebar.classList.toggle('show');
      document.body.classList.toggle('sidebar-active');
      
      // Toggle aria-expanded attribute for accessibility
      var isExpanded = sidebar.classList.contains('show');
      this.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
      
      console.log('Sidebar visibility toggled:', isExpanded ? 'shown' : 'hidden');
    });
    
    // Add a click handler to the document to close sidebar when clicking outside
    document.addEventListener('click', function(e) {
      // Only do this on mobile
      if (window.innerWidth > 991.98) return;
      
      // Check if sidebar is visible and click is outside sidebar and hamburger
      if (sidebar.classList.contains('show') && 
          !sidebar.contains(e.target) && 
          !newHamburgerButton.contains(e.target)) {
        
        // Hide sidebar
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
        newHamburgerButton.setAttribute('aria-expanded', 'false');
      }
    });
  });
})();

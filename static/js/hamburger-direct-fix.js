/**
 * Ultra simple hamburger toggle fix
 * This is a direct fix that doesn't rely on any other code
 */

// Run immediately on page load - no need for DOMContentLoaded
(function() {
  // Create a self-executing function to avoid global variables
  function initHamburgerFix() {
    // Get the hamburger button and sidebar elements directly
    var hamburger = document.querySelector('.navbar-toggler');
    var sidebar = document.querySelector('.sidebar');
    
    if (!hamburger || !sidebar) {
      console.error('Could not find hamburger button or sidebar');
      return;
    }
    
    // Simple toggle function that directly manipulates the DOM
    function toggleSidebar(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      // Simply toggle classes directly
      if (sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
      } else {
        sidebar.classList.add('show');
        document.body.classList.add('sidebar-active');
      }
    }
    
    // Remove existing click listeners and add our direct one
    hamburger.outerHTML = hamburger.outerHTML;
    hamburger = document.querySelector('.navbar-toggler');
    hamburger.addEventListener('click', toggleSidebar);
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(e) {
      if (sidebar.classList.contains('show') && 
          !sidebar.contains(e.target) &&
          !hamburger.contains(e.target)) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
      }
    });
  }
  
  // Run the function immediately, but also wait for DOM if needed
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHamburgerFix);
  } else {
    initHamburgerFix();
  }
})();

/**
 * Ultra simple hamburger button fix
 */

// Execute immediately when script is loaded
(function() {
  // Function to find and setup the hamburger button
  function setupHamburgerButton() {
    console.log('Setting up hamburger button');
    
    // Get the hamburger button and sidebar
    const hamburger = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    
    // Exit if elements don't exist
    if (!hamburger || !sidebar) {
      console.error('Hamburger button or sidebar not found');
      return;
    }

    // Remove any existing click listeners by replacing the element
    const newHamburger = hamburger.cloneNode(true);
    hamburger.parentNode.replaceChild(newHamburger, hamburger);
    
    // Add our simple click handler
    newHamburger.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log('Hamburger clicked');
      
      // Simply toggle the show class on the sidebar
      if (sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
      } else {
        sidebar.classList.add('show');
        document.body.classList.add('sidebar-active');
      }
    });
  }
  
  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupHamburgerButton);
  } else {
    setupHamburgerButton();
  }
})();

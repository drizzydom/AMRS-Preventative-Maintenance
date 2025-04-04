/**
 * UNIFIED SIDEBAR TOGGLE
 * Complete solution that removes duplicate buttons and ensures toggle works
 */
(function() {
  // Run this script immediately to avoid any flashing/jumping

  // 1. First, remove ALL existing toggle buttons to avoid duplicates
  function removeExistingButtons() {
    document.querySelectorAll('.sidebar-toggle-item, .sidebar-toggle-btn, .simple-sidebar-toggle, [class*="sidebar-toggle"]').forEach(function(btn) {
      if (btn && btn.parentNode) {
        btn.parentNode.removeChild(btn);
      }
    });
  }
  
  // 2. Create a single, clean toggle button
  function createToggleButton() {
    const button = document.createElement('button');
    button.id = 'unified-sidebar-toggle';
    button.className = 'unified-sidebar-toggle';
    button.innerHTML = '<i class="fas fa-bars"></i>';
    button.setAttribute('aria-label', 'Toggle sidebar');
    button.style.cssText = 'position:absolute;top:10px;left:10px;z-index:9999;background:transparent;border:none;color:white;font-size:1.2rem;cursor:pointer;width:30px;height:30px;padding:0;border-radius:4px;';
    
    // Add hover effect
    button.addEventListener('mouseenter', function() {
      this.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
    });
    button.addEventListener('mouseleave', function() {
      this.style.backgroundColor = 'transparent';
    });
    
    // Add it to the sidebar in a fixed position
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      sidebar.style.paddingTop = '40px'; // Make room for the button
      sidebar.insertBefore(button, sidebar.firstChild);
      
      // Ensure button stays visible when scrolling sidebar
      sidebar.addEventListener('scroll', function() {
        button.style.top = (sidebar.scrollTop + 10) + 'px';
      });
    }
    
    return button;
  }
  
  // 3. Implement the actual toggle functionality
  function setupToggleFunctionality(button) {
    // This is our ONE true toggle function
    function doToggleSidebar() {
      // Toggle the class
      document.body.classList.toggle('sidebar-collapsed');
      
      // Update icon to indicate state
      const icon = button.querySelector('i');
      if (document.body.classList.contains('sidebar-collapsed')) {
        if (icon) icon.className = 'fas fa-chevron-right';
        localStorage.setItem('sidebar-collapsed', 'true');
        
        // Apply CSS changes directly for immediate effect
        document.querySelectorAll('.sidebar').forEach(sidebar => {
          sidebar.style.width = '50px';
        });
        
        document.querySelectorAll('.content-container, .main-content, .col-md-9, .col-lg-10').forEach(content => {
          content.style.marginLeft = '50px';
          content.style.width = 'calc(100% - 50px)';
          content.style.maxWidth = 'calc(100% - 50px)';
        });
        
      } else {
        if (icon) icon.className = 'fas fa-bars';
        localStorage.removeItem('sidebar-collapsed');
        
        // Apply CSS changes directly for immediate effect
        document.querySelectorAll('.sidebar').forEach(sidebar => {
          sidebar.style.width = '200px';
        });
        
        document.querySelectorAll('.content-container, .main-content, .col-md-9, .col-lg-10').forEach(content => {
          content.style.marginLeft = '200px';
          content.style.width = 'calc(100% - 200px)';
          content.style.maxWidth = 'calc(100% - 200px)';
        });
      }
      
      // Notify any other scripts that might be listening
      window.dispatchEvent(new Event('sidebar-toggled'));
    }
    
    // Set up the click handler
    button.addEventListener('click', doToggleSidebar);
    
    // Override any existing toggle functions to use our implementation
    window.toggleSidebar = doToggleSidebar;
  }
  
  // 4. Apply saved state from localStorage
  function applySavedState() {
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
      document.body.classList.add('sidebar-collapsed');
      
      // Apply CSS changes directly
      document.querySelectorAll('.sidebar').forEach(sidebar => {
        sidebar.style.width = '50px';
      });
      
      document.querySelectorAll('.content-container, .main-content, .col-md-9, .col-lg-10').forEach(content => {
        content.style.marginLeft = '50px';
        content.style.width = 'calc(100% - 50px)';
        content.style.maxWidth = 'calc(100% - 50px)';
      });
      
      // Update the button icon if it exists
      const button = document.getElementById('unified-sidebar-toggle');
      if (button) {
        const icon = button.querySelector('i');
        if (icon) icon.className = 'fas fa-chevron-right';
      }
    }
  }
  
  // Execute the solution immediately
  removeExistingButtons();
  const toggleButton = createToggleButton();
  setupToggleFunctionality(toggleButton);
  
  // Apply the saved state after a very short delay to ensure DOM elements exist
  setTimeout(applySavedState, 10);
  
  // Disable any other toggle scripts that might run later
  window.sidebarToggleApplied = true;
})();

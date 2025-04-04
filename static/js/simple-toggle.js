/**
 * ULTRA SIMPLE SIDEBAR TOGGLE
 * No dependencies, no complex logic - just direct DOM manipulation
 */
(function() {
  // Run immediately - don't wait for DOMContentLoaded
  function createToggleButton() {
    // Create a simple button element
    const button = document.createElement('button');
    button.className = 'simple-sidebar-toggle';
    button.innerHTML = '<i class="fas fa-bars"></i>';
    button.style.cssText = 'position:absolute;top:10px;left:10px;z-index:9999;background:transparent;border:none;color:white;font-size:1.2rem;cursor:pointer;width:30px;height:30px;padding:0;';
    
    // Add it to the sidebar
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      sidebar.style.paddingTop = '40px'; // Make room for the button
      sidebar.insertBefore(button, sidebar.firstChild);
      
      // Add the click handler directly
      button.onclick = function() {
        document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed') ? 'true' : 'false');
      };
    }
  }
  
  // Apply collapsed state from localStorage
  function applySavedState() {
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
      document.body.classList.add('sidebar-collapsed');
    }
  }
  
  // Run immediately
  createToggleButton();
  applySavedState();
  
  // Also run on DOMContentLoaded as a fallback
  document.addEventListener('DOMContentLoaded', function() {
    createToggleButton();
    applySavedState();
  });
})();

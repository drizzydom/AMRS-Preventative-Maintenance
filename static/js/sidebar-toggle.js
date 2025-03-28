/**
 * Sidebar Toggle Functionality
 * Handles collapsing and expanding the sidebar
 */

document.addEventListener('DOMContentLoaded', function() {
    // Create sidebar toggle button
    createSidebarToggle();
    
    // Check for saved sidebar state
    loadSidebarState();
    
    // Set up event listener for window resize
    window.addEventListener('resize', handleWindowResize);
    
    // Handle initial window size
    handleWindowResize();
});

// Create sidebar toggle button dynamically
function createSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'sidebar-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    toggleBtn.setAttribute('aria-label', 'Toggle Sidebar');
    toggleBtn.addEventListener('click', toggleSidebar);
    
    document.body.appendChild(toggleBtn);
}

// Toggle sidebar expanded/collapsed state
function toggleSidebar() {
    const body = document.body;
    
    // Toggle collapsed class
    body.classList.toggle('sidebar-collapsed');
    
    // Store preference in localStorage
    if (body.classList.contains('sidebar-collapsed')) {
        localStorage.setItem('sidebar-collapsed', 'true');
    } else {
        localStorage.removeItem('sidebar-collapsed');
    }
}

// Load saved sidebar state from localStorage
function loadSidebarState() {
    const body = document.body;
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        body.classList.add('sidebar-collapsed');
    }
}

// Auto-collapse sidebar on smaller screens
function handleWindowResize() {
    const body = document.body;
    const width = window.innerWidth;
    
    // Auto-collapse on medium screens
    if (width < 1200 && width >= 992) {
        body.classList.add('sidebar-collapsed');
    } 
    // Only restore if user hasn't manually set a preference
    else if (width >= 1200 && !localStorage.getItem('sidebar-collapsed')) {
        body.classList.remove('sidebar-collapsed');
    }
}

/**
 * Sidebar Toggle Functionality
 * Handles collapsing and expanding the sidebar
 */

document.addEventListener('DOMContentLoaded', function() {
    // Create sidebar toggle button inside the sidebar
    createSidebarToggle();
    
    // Add data-title attributes to all sidebar links for tooltips
    addTooltipAttributes();
    
    // Check for saved sidebar state
    loadSidebarState();
    
    // Set up event listener for window resize
    window.addEventListener('resize', handleWindowResize);
    
    // Handle initial window size
    handleWindowResize();

    // Toggle sidebar on mobile
    const sidebarToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar-container');
    const body = document.body;
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            body.classList.toggle('sidebar-active');
            
            // Toggle collapsed class for icon-only display
            document.querySelector('.sidebar').classList.toggle('collapsed');
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const isClickInside = sidebar?.contains(event.target) || 
                             sidebarToggle?.contains(event.target);
        
        if (!isClickInside && sidebar?.classList.contains('show')) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
            document.querySelector('.sidebar')?.classList.remove('collapsed');
        }
    });
});

// Add data-title attributes to sidebar links for tooltips
function addTooltipAttributes() {
    // Add tooltip data to regular sidebar links
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        const text = link.querySelector('.sidebar-link-text')?.textContent.trim();
        if (text) {
            link.setAttribute('data-title', text);
        }
    });
    
    // Add tooltip data to logout button
    const logoutBtn = document.querySelector('.sidebar-logout-btn');
    if (logoutBtn) {
        const text = logoutBtn.querySelector('span')?.textContent.trim();
        if (text) {
            logoutBtn.setAttribute('data-title', text);
        }
    }
}

// Create sidebar toggle button dynamically and place in sidebar
function createSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    // Create toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'sidebar-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    toggleBtn.setAttribute('aria-label', 'Toggle Sidebar');
    toggleBtn.setAttribute('title', 'Toggle Sidebar');
    toggleBtn.addEventListener('click', toggleSidebar);
    
    // Create container at the top of sidebar for the toggle
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'sidebar-toggle-container';
    
    // Add the button to the container
    toggleContainer.appendChild(toggleBtn);
    
    // Insert at the beginning of the sidebar
    sidebar.insertBefore(toggleContainer, sidebar.firstChild);
}

// Toggle sidebar expanded/collapsed state
function toggleSidebar() {
    const body = document.body;
    
    // Toggle collapsed class
    body.classList.toggle('sidebar-collapsed');
    
    // Apply collapsed class to sidebar element as well for consistent styling
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        if (body.classList.contains('sidebar-collapsed')) {
            sidebar.classList.add('collapsed');
            // Rotate icon to point right when collapsed
            const icon = document.querySelector('.sidebar-toggle i');
            if (icon) icon.className = 'fas fa-chevron-right';
        } else {
            sidebar.classList.remove('collapsed');
            // Rotate icon to point left when expanded
            const icon = document.querySelector('.sidebar-toggle i');
            if (icon) icon.className = 'fas fa-chevron-left';
        }
    }
    
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
    const sidebar = document.querySelector('.sidebar');
    
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        body.classList.add('sidebar-collapsed');
        if (sidebar) {
            sidebar.classList.add('collapsed');
            // Set correct icon on page load
            const icon = document.querySelector('.sidebar-toggle i');
            if (icon) icon.className = 'fas fa-chevron-right';
        }
    }
}

// Auto-collapse sidebar on smaller screens
function handleWindowResize() {
    const body = document.body;
    const width = window.innerWidth;
    
    // Auto-collapse on medium screens
    if (width < 1200 && width >= 992) {
        body.classList.add('sidebar-collapsed');
        
        // Make sure the toggle button shows the correct icon
        const icon = document.querySelector('.sidebar-toggle i');
        if (icon) icon.className = 'fas fa-chevron-right';
    } 
    // Only restore if user hasn't manually set a preference
    else if (width >= 1200 && !localStorage.getItem('sidebar-collapsed')) {
        body.classList.remove('sidebar-collapsed');
        
        // Make sure the toggle button shows the correct icon
        const icon = document.querySelector('.sidebar-toggle i');
        if (icon) icon.className = 'fas fa-chevron-left';
    }
}

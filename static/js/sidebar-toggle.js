/**
 * Improved Sidebar Toggle Functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add data-title attributes to sidebar links for tooltips
    addTooltipAttributes();
    
    // Check for saved sidebar state
    loadSidebarState();
    
    // Set up event listener for window resize
    window.addEventListener('resize', handleWindowResize);
    
    // Handle initial window size
    handleWindowResize();

    // Toggle sidebar on mobile
    const sidebarToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(event) {
            event.stopPropagation(); // Prevent event from bubbling up
            
            if (window.innerWidth <= 991.98) { // Only for mobile view
                sidebar.classList.toggle('show');
                body.classList.toggle('sidebar-active');
            }
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const isInsideSidebar = sidebar?.contains(event.target);
        const isToggleButton = sidebarToggle?.contains(event.target);
        
        // If click is outside sidebar and toggle, and sidebar is shown on mobile
        if (!isInsideSidebar && !isToggleButton && sidebar?.classList.contains('show') && window.innerWidth <= 991.98) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
        }
    });
    
    // Prevent clicks inside sidebar from closing it
    sidebar?.addEventListener('click', function(event) {
        event.stopPropagation();
    });
    
    // Close sidebar when pressing escape key on mobile
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar?.classList.contains('show') && window.innerWidth <= 991.98) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
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

// Toggle sidebar expanded/collapsed state - desktop only
function toggleSidebar() {
    if (window.innerWidth <= 991.98) {
        return; // Don't use this function on mobile
    }
    
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

// Load saved sidebar state from localStorage - desktop only
function loadSidebarState() {
    const body = document.body;
    
    if (localStorage.getItem('sidebar-collapsed') === 'true' && window.innerWidth > 991.98) {
        body.classList.add('sidebar-collapsed');
    }
}

// Auto-collapse sidebar on smaller screens, use different approach on mobile
function handleWindowResize() {
    const body = document.body;
    const sidebar = document.querySelector('.sidebar');
    const width = window.innerWidth;
    
    // Mobile view
    if (width <= 991.98) {
        // Remove desktop collapsed class as it's not needed
        body.classList.remove('sidebar-collapsed');
        
        // Hide sidebar by default on mobile
        sidebar?.classList.remove('show');
        body.classList.remove('sidebar-active');
    } 
    // Medium screens - auto-collapse
    else if (width < 1200 && width >= 992) {
        body.classList.add('sidebar-collapsed');
    } 
    // Large screens - restore user preference
    else if (width >= 1200) {
        if (localStorage.getItem('sidebar-collapsed') === 'true') {
            body.classList.add('sidebar-collapsed');
        } else {
            body.classList.remove('sidebar-collapsed');
        }
    }
}

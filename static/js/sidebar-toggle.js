/**
 * Improved Sidebar Toggle Functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add data-title attributes to sidebar links for tooltips
    addTooltipAttributes();
    
    // Important: Load sidebar state BEFORE handling window resize
    // This ensures user preference is respected before any auto-adjustments
    loadSidebarState();
    
    // Handle initial window size
    handleWindowResize(true); // Pass true to indicate initial load
    
    // Set up event listener for window resize
    window.addEventListener('resize', function() {
        handleWindowResize(false); // Pass false to indicate resize event
    });

    // Toggle sidebar on mobile - improved handling
    const sidebarToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default behavior
            event.stopPropagation(); // Prevent event from bubbling up
            
            if (window.innerWidth <= 767.98) { // Mobile view threshold
                sidebar.classList.toggle('show');
                body.classList.toggle('sidebar-active');
                
                // Add ARIA attributes for accessibility
                const isExpanded = sidebar.classList.contains('show');
                sidebarToggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
            }
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const isInsideSidebar = sidebar?.contains(event.target);
        const isToggleButton = sidebarToggle?.contains(event.target);
        
        // If click is outside sidebar and toggle, and sidebar is shown on mobile
        if (!isInsideSidebar && !isToggleButton && sidebar?.classList.contains('show') && window.innerWidth <= 767.98) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
            
            // Update ARIA attributes
            if (sidebarToggle) {
                sidebarToggle.setAttribute('aria-expanded', 'false');
            }
        }
    });
    
    // Prevent clicks inside sidebar from closing it
    sidebar?.addEventListener('click', function(event) {
        event.stopPropagation();
    });
    
    // Close sidebar when pressing escape key on mobile
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar?.classList.contains('show') && window.innerWidth <= 767.98) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
            
            if (sidebarToggle) {
                sidebarToggle.setAttribute('aria-expanded', 'false');
            }
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
    const userPreference = localStorage.getItem('sidebar-collapsed');
    
    // Only apply stored preference on desktop
    if (userPreference === 'true' && window.innerWidth > 991.98) {
        body.classList.add('sidebar-collapsed');
    } else if (userPreference !== 'true' && window.innerWidth > 991.98) {
        body.classList.remove('sidebar-collapsed');
    }
}

// Auto-collapse sidebar on smaller screens, use different approach on mobile
function handleWindowResize(isInitialLoad) {
    const body = document.body;
    const width = window.innerWidth;
    const userPreference = localStorage.getItem('sidebar-collapsed');
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('.navbar-toggler');
    
    // Mobile view - implement drawer pattern
    if (width <= 767.98) {
        // Remove desktop collapsed class as it's not needed
        body.classList.remove('sidebar-collapsed');
        
        // Hide sidebar by default on mobile
        if (sidebar) {
            sidebar.classList.remove('show');
            body.classList.remove('sidebar-active');
        }
        
        // Make sure toggle button has correct ARIA attribute
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
        
        // Add close button to sidebar if it doesn't exist yet
        addCloseButtonIfNeeded(sidebar);
    } 
    // Small/Medium screens - auto-collapse ONLY if initial load or no preference
    else if (width < 1200 && width >= 768) {
        // Remove any mobile close buttons when in desktop view
        removeCloseButton(sidebar);
        
        if (isInitialLoad && userPreference === null) {
            // Only auto-collapse on medium screens if no user preference exists
            body.classList.add('sidebar-collapsed');
            // Don't save this auto-preference to localStorage
        } else if (userPreference === 'true') {
            // Honor user's preference if they've explicitly collapsed
            body.classList.add('sidebar-collapsed');
        } else if (userPreference === null && !isInitialLoad) {
            // If resizing to medium screen and no preference, don't change current state
        } else {
            // If user explicitly wants expanded sidebar, respect that
            body.classList.remove('sidebar-collapsed');
        }
    } 
    // Large screens - always restore user preference
    else if (width >= 1200) {
        // Remove any mobile close buttons when in desktop view
        removeCloseButton(sidebar);
        
        if (userPreference === 'true') {
            body.classList.add('sidebar-collapsed');
        } else {
            body.classList.remove('sidebar-collapsed');
        }
    }
}

// Helper function to add close button only if it doesn't exist
function addCloseButtonIfNeeded(sidebar) {
    if (!sidebar || sidebar.querySelector('.sidebar-back-btn')) {
        return; // Return if sidebar is null or close button already exists
    }
    
    const sidebarHeader = document.createElement('div');
    sidebarHeader.className = 'sidebar-header';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'sidebar-back-btn';
    closeButton.innerHTML = '<i class="fas fa-arrow-left"></i> Close Menu';
    closeButton.setAttribute('aria-label', 'Close sidebar');
    
    closeButton.addEventListener('click', function() {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
        
        const sidebarToggle = document.querySelector('.navbar-toggler');
        if (sidebarToggle) {
            sidebarToggle.setAttribute('aria-expanded', 'false');
        }
    });
    
    sidebarHeader.appendChild(closeButton);
    
    // Insert at the beginning of sidebar
    if (sidebar.firstChild) {
        sidebar.insertBefore(sidebarHeader, sidebar.firstChild);
    } else {
        sidebar.appendChild(sidebarHeader);
    }
}

// Helper function to remove close button on larger screens
function removeCloseButton(sidebar) {
    if (!sidebar) return;
    
    const closeButton = sidebar.querySelector('.sidebar-header');
    if (closeButton) {
        closeButton.remove();
    }
}

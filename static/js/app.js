/**
 * Main application JavaScript
 * Handles common functionality across all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-hide alert messages after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-important)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(event) {
            if (!confirm(this.dataset.confirm)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
    
    // Set up Form validation 
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Handle mobile navigation
    var navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            var navbarCollapse = document.querySelector('.navbar-collapse');
            if (!navbarToggler.classList.contains('collapsed')) {
                navbarToggler.classList.add('collapsed');
                navbarCollapse.classList.remove('show');
            } else {
                navbarToggler.classList.remove('collapsed');
                navbarCollapse.classList.add('show');
            }
        });
    }
    
    // Handle dark mode toggle if available
    var darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            var html = document.documentElement;
            if (html.getAttribute('data-theme') === 'dark') {
                html.removeAttribute('data-theme');
                localStorage.removeItem('theme');
            } else {
                html.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        });
        
        // Check for saved theme preference
        var savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    }
    
    // Restore sidebar collapsed state from localStorage on desktop
    if (window.innerWidth >= 992) {
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsed) {
            document.body.classList.add('sidebar-collapsed');
            
            // Update icon if needed
            var collapseIcon = document.querySelector('.sidebar-toggle-item.d-none.d-lg-block .fas');
            if (collapseIcon) {
                collapseIcon.classList.remove('fa-angle-double-left');
                collapseIcon.classList.add('fa-angle-double-right');
            }
        }
    }
});

// Helper function for AJAX requests
function fetchApi(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        });
}

// Format date helper
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Updated toggleSidebar function to only use hamburger button
function toggleSidebar() {
    var sidebar = document.querySelector('.sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    
    if (!sidebar || window.innerWidth >= 992) return; // Only handle on mobile
    
    // Toggle sidebar visibility
    sidebar.classList.toggle('show');
    document.body.classList.toggle('sidebar-active');
    
    // Show/hide overlay
    if (overlay) {
        if (sidebar.classList.contains('show')) {
            overlay.style.display = 'block';
        } else {
            overlay.style.display = 'none';
        }
    }
    
    // Toggle hamburger button appearance
    var hamburgerBtn = document.getElementById('hamburger-btn');
    if (hamburgerBtn) {
        if (sidebar.classList.contains('show')) {
            hamburgerBtn.setAttribute('aria-expanded', 'true');
        } else {
            hamburgerBtn.setAttribute('aria-expanded', 'false');
        }
    }
}

// Handle hamburger button click
document.addEventListener('DOMContentLoaded', function() {
    // Connect hamburger button to toggle function
    var hamburgerBtn = document.getElementById('hamburger-btn');
    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // Handle overlay click to close sidebar
    var overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            toggleSidebar();
        });
    }
    
    // Ensure sidebar is hidden on mobile by default
    var sidebar = document.querySelector('.sidebar');
    if (sidebar && window.innerWidth < 992) {
        sidebar.classList.remove('show');
        document.body.classList.remove('sidebar-active');
    }
});

// Update toggleSidebarCollapse function to save state to localStorage
function toggleSidebarCollapse() {
    // Only allow sidebar collapse on desktop (screens >= 992px)
    if (window.innerWidth < 992) {
        return; // Exit the function early on mobile devices
    }
    
    document.body.classList.toggle('sidebar-collapsed');
    
    // Save sidebar collapsed state to localStorage
    localStorage.setItem('sidebar-collapsed', document.body.classList.contains('sidebar-collapsed'));
    
    // Update the icon direction based on collapsed state
    var collapseIcon = document.querySelector('.sidebar-toggle-item.d-none.d-lg-block .fas');
    if (collapseIcon) {
        if (document.body.classList.contains('sidebar-collapsed')) {
            collapseIcon.classList.remove('fa-angle-double-left');
            collapseIcon.classList.add('fa-angle-double-right');
        } else {
            collapseIcon.classList.remove('fa-angle-double-right');
            collapseIcon.classList.add('fa-angle-double-left');
        }
    }
}

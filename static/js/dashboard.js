/**
 * Ultra-minimal dashboard JavaScript functionality
 * Handles site filtering and part visibility toggling
 */

// Store original stats values when page loads
let originalStats = {};

// Function to run when DOM is loaded
function dashboardInit() {
    console.log("Dashboard init running");
    
    // 1. Store original stats values
    storeOriginalStats();
    
    // 2. Set up site filter
    setupSiteFilter();
    
    // 3. Set up toggle all parts button
    setupToggleAllParts();
    
    // 4. Set up individual toggle buttons
    setupPartToggles();
    
    // 5. Show all parts initially (instead of hiding them)
    showAllParts();
    
    // 6. Update button text to match the initial state (all parts are now shown)
    updateToggleButtonText(true);
    
    console.log("Dashboard initialization complete");
}

// Store original stats values
function storeOriginalStats() {
    const overdueElement = document.querySelector('.stats-danger .stats-value');
    const dueSoonElement = document.querySelector('.stats-warning .stats-value');
    const okElement = document.querySelector('.stats-success .stats-value');
    const totalElement = document.querySelector('.stats-primary .stats-value');
    
    if (overdueElement) originalStats.overdue = overdueElement.textContent;
    if (dueSoonElement) originalStats.dueSoon = dueSoonElement.textContent;
    if (okElement) originalStats.ok = okElement.textContent;
    if (totalElement) originalStats.total = totalElement.textContent;
    
    console.log("Original stats stored:", originalStats);
}

// Set up site filter
function setupSiteFilter() {
    const siteFilter = document.getElementById('site-filter');
    if (!siteFilter) return;
    
    siteFilter.addEventListener('change', function() {
        const siteId = this.value;
        filterSites(siteId);
    });
}

// Filter sites by ID
function filterSites(siteId) {
    console.log(`Filtering by site ID: ${siteId}`);
    
    // Update filter text display
    const currentFilter = document.getElementById('current-filter');
    if (currentFilter) {
        if (siteId === 'all') {
            currentFilter.textContent = 'All Sites';
        } else {
            const siteFilter = document.getElementById('site-filter');
            const option = siteFilter.querySelector(`option[value="${siteId}"]`);
            currentFilter.textContent = option ? option.textContent : '';
        }
    }
    
    // Handle site filtering
    if (siteId === 'all') {
        // Show all rows with site IDs
        document.querySelectorAll('[data-site-id]').forEach(function(row) {
            row.style.display = '';
        });
        // Show all Overdue/Due Soon cards
        showCardIfRowsExist('overdue');
        showCardIfRowsExist('due-soon');
        // Reset counters to original values
        resetCounters();
    } else {
        // Hide all rows with site IDs
        document.querySelectorAll('[data-site-id]').forEach(function(row) {
            row.style.display = 'none';
        });
        // Show rows matching the selected site
        document.querySelectorAll(`[data-site-id="${siteId}"]`).forEach(function(row) {
            row.style.display = '';
        });
        // Show/hide Overdue/Due Soon cards based on visible rows
        showCardIfRowsExist('overdue');
        showCardIfRowsExist('due-soon');
        // Show the site item in the accordion
        const siteItem = document.querySelector(`.site-item[data-site-id="${siteId}"]`);
        if (siteItem) {
            siteItem.style.display = '';
            // Update counters for just this site
            updateCountersFromSite(siteItem);
        }
    }
}

// Helper to show/hide Overdue/Due Soon cards based on visible rows
function showCardIfRowsExist(type) {
    let cardSelector, rowSelector;
    if (type === 'overdue') {
        cardSelector = '.stats-danger, .card:has(.fa-exclamation-triangle)';
        rowSelector = 'tr[data-site-id]';
    } else if (type === 'due-soon') {
        cardSelector = '.stats-warning, .card:has(.fa-clock)';
        rowSelector = 'tr[data-site-id]';
    } else {
        return;
    }
    // Find the card
    const cards = Array.from(document.querySelectorAll(cardSelector)).filter(card => card.querySelector(rowSelector));
    cards.forEach(card => {
        // Only check tables inside cards
        const table = card.querySelector('table');
        if (!table) return;
        // Count visible rows
        const visibleRows = Array.from(table.querySelectorAll('tbody tr')).filter(row => row.style.display !== 'none');
        if (visibleRows.length === 0) {
            card.style.display = 'none';
        } else {
            card.style.display = '';
        }
    });
}

// Reset stats counters to original values
function resetCounters() {
    const overdueElement = document.querySelector('.stats-danger .stats-value');
    const dueSoonElement = document.querySelector('.stats-warning .stats-value');
    const okElement = document.querySelector('.stats-success .stats-value');
    const totalElement = document.querySelector('.stats-primary .stats-value');
    
    if (overdueElement && originalStats.overdue) overdueElement.textContent = originalStats.overdue;
    if (dueSoonElement && originalStats.dueSoon) dueSoonElement.textContent = originalStats.dueSoon;
    if (okElement && originalStats.ok) okElement.textContent = originalStats.ok;
    if (totalElement && originalStats.total) totalElement.textContent = originalStats.total;
}

// Update counters based on site
function updateCountersFromSite(siteItem) {
    // Find site status badges
    let overdueCount = 0;
    let dueSoonCount = 0;
    let okCount = 0;
    
    // Extract site status from badge texts
    const overdueText = siteItem.querySelector('.badge.bg-danger')?.textContent || '';
    const dueSoonText = siteItem.querySelector('.badge.bg-warning')?.textContent || '';
    
    // Parse numbers from badge texts
    const overdueMatch = overdueText.match(/(\d+)/);
    const dueSoonMatch = dueSoonText.match(/(\d+)/);
    
    if (overdueMatch) overdueCount = parseInt(overdueMatch[1]);
    if (dueSoonMatch) dueSoonCount = parseInt(dueSoonMatch[1]);
    
    // Count OK parts or assume all remaining parts are OK
    const okBadge = siteItem.querySelector('.badge.bg-success');
    if (okBadge && okBadge.textContent.includes('All Parts OK')) {
        const partRows = siteItem.querySelectorAll('.machine-parts-row tr');
        okCount = partRows.length;
    } else {
        // Count OK badges
        siteItem.querySelectorAll('.badge.bg-success').forEach(function() {
            okCount++;
        });
    }
    
    // Update counter displays
    const overdueElement = document.querySelector('.stats-danger .stats-value');
    const dueSoonElement = document.querySelector('.stats-warning .stats-value');
    const okElement = document.querySelector('.stats-success .stats-value');
    const totalElement = document.querySelector('.stats-primary .stats-value');
    
    if (overdueElement) overdueElement.textContent = overdueCount;
    if (dueSoonElement) dueSoonElement.textContent = dueSoonCount;
    if (okElement) okElement.textContent = okCount;
    if (totalElement) totalElement.textContent = overdueCount + dueSoonCount + okCount;
}

// Set up toggle all parts button
function setupToggleAllParts() {
    const toggleBtn = document.getElementById('toggleAllMachineParts');
    if (!toggleBtn) return;
    
    toggleBtn.addEventListener('click', function() {
        const allShowing = areAllPartsShowing();
        
        if (allShowing) {
            hideAllParts();
        } else {
            showAllParts();
        }
    });
    
    // Set initial button text based on parts visibility
    updateToggleButtonText(areAllPartsShowing());
}

// Check if all machine parts are shown
function areAllPartsShowing() {
    const partRows = document.querySelectorAll('.machine-parts-row');
    if (partRows.length === 0) return false;
    
    for (const row of partRows) {
        // Check if the row has the Bootstrap 'show' class
        if (!row.classList.contains('show')) {
            return false;
        }
    }
    return true;
}

// Hide all machine parts
function hideAllParts() {
    // Hide all part rows using Bootstrap's collapse
    document.querySelectorAll('.machine-parts-row').forEach(function(row) {
        if (bootstrap && bootstrap.Collapse) {
            const bsCollapse = bootstrap.Collapse.getInstance(row);
            if (bsCollapse) {
                bsCollapse.hide();
            } else {
                // Fallback to direct style manipulation if no collapse instance exists
                row.classList.remove('show');
            }
        } else {
            // Fallback in case bootstrap is not available
            row.style.display = 'none';
        }
    });
    
    // Reset toggle buttons
    document.querySelectorAll('.toggle-parts-btn').forEach(function(btn) {
        btn.setAttribute('aria-expanded', 'false');
        btn.classList.remove('active');
    });
    
    // Update toggle all button text and icon
    updateToggleButtonText(false);
}

// Show all machine parts
function showAllParts() {
    // Show all part rows using Bootstrap's collapse
    document.querySelectorAll('.machine-parts-row').forEach(function(row) {
        if (bootstrap && bootstrap.Collapse) {
            const bsCollapse = bootstrap.Collapse.getInstance(row) || new bootstrap.Collapse(row, { toggle: false });
            bsCollapse.show();
        } else {
            // Fallback in case bootstrap is not available
            row.classList.add('show');
            row.style.display = 'table-row';
        }
    });
    
    // Update toggle buttons
    document.querySelectorAll('.toggle-parts-btn').forEach(function(btn) {
        btn.setAttribute('aria-expanded', 'true');
        btn.classList.add('active');
    });
    
    // Update toggle all button text and icon
    updateToggleButtonText(true);
}

// Helper function to update the toggle button text and icon
function updateToggleButtonText(isShowing) {
    const toggleText = document.getElementById('toggleAllText');
    const toggleBtn = document.getElementById('toggleAllMachineParts');
    
    if (toggleText) {
        toggleText.textContent = isShowing ? 'Hide All Parts' : 'Show All Parts';
    }
    
    if (toggleBtn) {
        const icon = toggleBtn.querySelector('i');
        if (icon) {
            icon.className = isShowing ? 'fas fa-eye-slash me-1' : 'fas fa-eye me-1';
        }
    }
}

// Set up individual part toggle buttons
function setupPartToggles() {
    document.querySelectorAll('.toggle-parts-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const targetId = this.getAttribute('data-target');
            if (!targetId) return;
            
            const targetRow = document.querySelector(targetId);
            if (!targetRow) return;
            
            // Use Bootstrap's collapse functionality
            const bsCollapse = new bootstrap.Collapse(targetRow, {
                toggle: true
            });
            
            // Update the button state based on the row's visibility
            // We need to use an event listener because Bootstrap toggle is asynchronous
            targetRow.addEventListener('shown.bs.collapse', () => {
                this.setAttribute('aria-expanded', 'true');
                this.classList.add('active');
            });
            
            targetRow.addEventListener('hidden.bs.collapse', () => {
                this.setAttribute('aria-expanded', 'false');
                this.classList.remove('active');
            });
        });
    });
}

// Run multiple initialization strategies to ensure the script runs at the right time
document.addEventListener('DOMContentLoaded', dashboardInit);
window.addEventListener('load', dashboardInit);

// Also run immediately if the document is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(dashboardInit, 0);
}

// Force dashboard initialization when page is shown (for browsers using back/forward navigation)
window.addEventListener('pageshow', function() {
    dashboardInit();
});

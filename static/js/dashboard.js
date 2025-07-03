/**
 * Ultra-minimal dashboard JavaScript functionality
 * Handles site filtering and part visibility toggling
 */

// Store original stats values when page loads
let originalStats = {};

// Initialize machine statuses on page load
function initializeMachineStatuses() {
    console.log("Initializing machine statuses");
    
    // Update all site containers
    document.querySelectorAll('.site-item').forEach(function(siteItem) {
        updateMachineStatuses(siteItem);
    });
}

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
    
    // 7. Initialize machine statuses based on their parts
    initializeMachineStatuses();
    
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
        
        // Show all site items
        document.querySelectorAll('.site-item').forEach(function(siteItem) {
            siteItem.style.display = '';
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
        
        // Hide all site items first
        document.querySelectorAll('.site-item').forEach(function(siteItem) {
            siteItem.style.display = 'none';
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
            
            // Update machine statuses based on the visible parts
            updateMachineStatuses(siteItem);
            
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
    let totalCount = 0;
    
    // Extract site status from badge texts
    const statusSummary = siteItem.querySelector('.site-stats-summary');
    const overdueText = statusSummary?.querySelector('.badge.bg-danger')?.textContent || '';
    const dueSoonText = statusSummary?.querySelector('.badge.bg-warning')?.textContent || '';
    
    // Parse numbers from badge texts
    const overdueMatch = overdueText.match(/(\d+)/);
    const dueSoonMatch = dueSoonText.match(/(\d+)/);
    
    if (overdueMatch) overdueCount = parseInt(overdueMatch[1]);
    if (dueSoonMatch) dueSoonCount = parseInt(dueSoonMatch[1]);
    
    // Count all parts in this site to get OK parts and total parts
    const partStatusBadges = siteItem.querySelectorAll('.parts-table-container .badge');
    let countedParts = 0;
    
    partStatusBadges.forEach(function(badge) {
        countedParts++;
        if (badge.classList.contains('bg-success')) {
            okCount++;
        }
    });
    
    // If we couldn't find any part status badges, calculate OK as remaining parts
    if (countedParts === 0) {
        // If "All Parts OK" badge is shown and no other status badges exist
        const allOkBadge = statusSummary?.querySelector('.badge.bg-success');
        if (allOkBadge && allOkBadge.textContent.includes('All Parts OK')) {
            // Get machine count and multiply by approx average parts per machine (fallback)
            const machineCountBadge = statusSummary?.querySelector('.badge.bg-primary');
            const machineCountMatch = machineCountBadge?.textContent.match(/(\d+)/);
            if (machineCountMatch) {
                const machineCount = parseInt(machineCountMatch[1]);
                // Estimate OK count based on machines, just to have a value
                okCount = machineCount;
            }
        }
    }
    
    // Calculate total parts for this site
    totalCount = overdueCount + dueSoonCount + okCount;
    
    // Update counter displays
    const overdueElement = document.querySelector('.stats-danger .stats-value');
    const dueSoonElement = document.querySelector('.stats-warning .stats-value');
    const okElement = document.querySelector('.stats-success .stats-value');
    const totalElement = document.querySelector('.stats-info .stats-value');
    
    if (overdueElement) overdueElement.textContent = overdueCount;
    if (dueSoonElement) dueSoonElement.textContent = dueSoonCount;
    if (okElement) okElement.textContent = okCount;
    if (totalElement) totalElement.textContent = totalCount;
}

// Update machine statuses for the selected site
function updateMachineStatuses(siteItem) {
    // Get all machines in this site
    const machineRows = siteItem.querySelectorAll('.machine-row');
    
    machineRows.forEach(function(machineRow) {
        // Find the machine's parts row to analyze its parts
        const machinePartsBtn = machineRow.querySelector('.toggle-parts-btn');
        if (!machinePartsBtn) return;
        
        const machineId = machinePartsBtn.getAttribute('data-target').substring(1);
        const partsRow = document.getElementById(machineId);
        
        if (partsRow) {
            // Count parts by status
            let overdueParts = 0;
            let dueSoonParts = 0;
            const partBadges = partsRow.querySelectorAll('.badge');
            
            partBadges.forEach(function(badge) {
                if (badge.classList.contains('bg-danger')) {
                    overdueParts++;
                } else if (badge.classList.contains('bg-warning')) {
                    dueSoonParts++;
                }
            });
            
            // Update the status cell with correct badges
            const statusCell = machineRow.querySelector('td:nth-child(3)');
            if (statusCell) {
                // Clear existing status badges
                statusCell.innerHTML = '';
                
                if (overdueParts > 0) {
                    const overdueBadge = document.createElement('span');
                    overdueBadge.className = 'badge bg-danger';
                    overdueBadge.textContent = `${overdueParts} Overdue`;
                    statusCell.appendChild(overdueBadge);
                    
                    // Update machine row class
                    machineRow.classList.remove('machine-status-ok', 'machine-status-due_soon');
                    machineRow.classList.add('machine-status-overdue');
                } else if (dueSoonParts > 0) {
                    const dueSoonBadge = document.createElement('span');
                    dueSoonBadge.className = 'badge bg-warning ms-1';
                    dueSoonBadge.textContent = `${dueSoonParts} Due Soon`;
                    statusCell.appendChild(dueSoonBadge);
                    
                    // Update machine row class
                    machineRow.classList.remove('machine-status-ok', 'machine-status-overdue');
                    machineRow.classList.add('machine-status-due_soon');
                } else {
                    // If no overdue or due soon parts, show "All OK"
                    const okBadge = document.createElement('span');
                    okBadge.className = 'badge bg-success';
                    okBadge.textContent = 'All OK';
                    statusCell.appendChild(okBadge);
                    
                    // Update machine row class
                    machineRow.classList.remove('machine-status-overdue', 'machine-status-due_soon');
                    machineRow.classList.add('machine-status-ok');
                }
            }
        }
    });
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
    // Also update all individual toggle buttons' aria-expanded and .active state
    document.querySelectorAll('.toggle-parts-btn').forEach(function(btn) {
        const targetId = btn.getAttribute('data-target');
        const targetRow = document.querySelector(targetId);
        if (targetRow) {
            const expanded = targetRow.classList.contains('show');
            btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
            btn.classList.toggle('active', expanded);
        }
    });
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
            let bsCollapse = bootstrap.Collapse.getInstance(targetRow);
            if (!bsCollapse) {
                bsCollapse = new bootstrap.Collapse(targetRow, { toggle: false });
            }
            if (targetRow.classList.contains('show')) {
                bsCollapse.hide();
            } else {
                bsCollapse.show();
            }
            // Update the button state based on the row's visibility
            targetRow.addEventListener('shown.bs.collapse', () => {
                this.setAttribute('aria-expanded', 'true');
                this.classList.add('active');
                updateToggleButtonText(areAllPartsShowing());
            }, { once: true });
            targetRow.addEventListener('hidden.bs.collapse', () => {
                this.setAttribute('aria-expanded', 'false');
                this.classList.remove('active');
                updateToggleButtonText(areAllPartsShowing());
            }, { once: true });
        });
    });
    // Add click handler for machine history buttons to redirect to maintenance records with filter
    document.querySelectorAll('.btn-machine-history').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const machineId = this.getAttribute('data-machine-id');
            if (machineId) {
                // Redirect to maintenance records with machine filter
                window.location.href = '/maintenance/records?machine_id=' + encodeURIComponent(machineId);
            }
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

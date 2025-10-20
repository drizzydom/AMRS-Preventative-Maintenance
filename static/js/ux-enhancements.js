/**
 * UX Enhancements JavaScript
 * Additional functionality for improved user experience
 */

// ===== 1. CLICKABLE STATUS CARDS =====
function initClickableStatusCards() {
    const statusCards = document.querySelectorAll('.stats-card[data-filter]');
    statusCards.forEach(card => {
        card.addEventListener('click', function() {
            const filter = this.dataset.filter;
            if (filter) {
                // Apply filter or navigate to filtered view
                if (filter === 'overdue') {
                    scrollToSection('overdue-section');
                } else if (filter === 'due-soon') {
                    scrollToSection('due-soon-section');
                } else if (filter === 'ok') {
                    scrollToSection('ok-section');
                }
            }
        });
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ===== 2. GLOBAL SEARCH =====
let searchTimeout = null;

function initGlobalSearch() {
    const searchInput = document.getElementById('global-search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            hideSearchResults();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.global-search')) {
            hideSearchResults();
        }
    });
}

function performSearch(query) {
    // Show loading state
    showSearchResults('<div class="search-result-item">Searching...</div>');
    
    // Perform search via API
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            showSearchResults('<div class="search-result-item">Error performing search</div>');
        });
}

function displaySearchResults(results) {
    if (!results || (results.machines.length === 0 && results.parts.length === 0 && results.sites.length === 0)) {
        showSearchResults('<div class="search-result-item">No results found</div>');
        return;
    }
    
    let html = '';
    
    // Machines
    if (results.machines && results.machines.length > 0) {
        results.machines.forEach(machine => {
            html += `
                <a href="/machines/${machine.id}" class="search-result-item" style="display: block; text-decoration: none; color: inherit;">
                    <span class="search-result-type machine">Machine</span>
                    <strong>${machine.name}</strong>
                    ${machine.site ? `<br><small class="text-muted">at ${machine.site}</small>` : ''}
                </a>
            `;
        });
    }
    
    // Parts
    if (results.parts && results.parts.length > 0) {
        results.parts.forEach(part => {
            html += `
                <a href="/parts/${part.id}" class="search-result-item" style="display: block; text-decoration: none; color: inherit;">
                    <span class="search-result-type part">Part</span>
                    <strong>${part.name}</strong>
                    ${part.machine ? `<br><small class="text-muted">on ${part.machine}</small>` : ''}
                </a>
            `;
        });
    }
    
    // Sites
    if (results.sites && results.sites.length > 0) {
        results.sites.forEach(site => {
            html += `
                <a href="/sites/${site.id}" class="search-result-item" style="display: block; text-decoration: none; color: inherit;">
                    <span class="search-result-type site">Site</span>
                    <strong>${site.name}</strong>
                </a>
            `;
        });
    }
    
    showSearchResults(html);
}

function showSearchResults(html) {
    let resultsDiv = document.getElementById('search-results');
    if (!resultsDiv) {
        resultsDiv = document.createElement('div');
        resultsDiv.id = 'search-results';
        resultsDiv.className = 'search-results';
        document.querySelector('.global-search').appendChild(resultsDiv);
    }
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

function hideSearchResults() {
    const resultsDiv = document.getElementById('search-results');
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
    }
}

// ===== 3. ACTION DROPDOWN =====
function initActionDropdowns() {
    document.addEventListener('click', function(e) {
        // Toggle dropdown
        if (e.target.closest('.action-dropdown-toggle')) {
            e.preventDefault();
            const dropdown = e.target.closest('.action-dropdown');
            const menu = dropdown.querySelector('.action-dropdown-menu');
            
            // Close other dropdowns
            document.querySelectorAll('.action-dropdown-menu.show').forEach(other => {
                if (other !== menu) {
                    other.classList.remove('show');
                }
            });
            
            menu.classList.toggle('show');
        }
        // Close dropdowns when clicking outside
        else if (!e.target.closest('.action-dropdown')) {
            document.querySelectorAll('.action-dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
}

// ===== 9. PROGRESSIVE DISCLOSURE =====
function initProgressiveDisclosure() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.details-toggle')) {
            e.preventDefault();
            const toggle = e.target.closest('.details-toggle');
            const contentId = toggle.dataset.target;
            const content = document.getElementById(contentId);
            
            if (content) {
                toggle.classList.toggle('expanded');
                content.classList.toggle('show');
            }
        }
    });
}

// ===== 12. CONFIRMATION DIALOGS =====
function initConfirmationDialogs() {
    // Enhanced delete confirmations
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('[data-confirm-delete]');
        if (deleteBtn) {
            e.preventDefault();
            const itemName = deleteBtn.dataset.itemName || 'this item';
            const itemType = deleteBtn.dataset.itemType || 'item';
            const consequence = deleteBtn.dataset.consequence || '';
            
            showConfirmationDialog(itemName, itemType, consequence, function() {
                // Proceed with deletion
                const form = deleteBtn.closest('form');
                if (form) {
                    form.submit();
                } else {
                    const href = deleteBtn.href;
                    if (href) {
                        window.location.href = href;
                    }
                }
            });
        }
    });
}

function showConfirmationDialog(itemName, itemType, consequence, onConfirm) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('confirmation-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'confirmation-modal';
        modal.className = 'modal fade confirmation-modal';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Confirm Deletion
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete <span class="confirmation-target-name"></span>?</p>
                        <div class="confirmation-consequence"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-2"></i>Cancel
                        </button>
                        <button type="button" class="btn btn-danger" id="confirm-delete-btn">
                            <i class="fas fa-trash me-2"></i>Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Update modal content
    modal.querySelector('.confirmation-target-name').textContent = itemName;
    const consequenceDiv = modal.querySelector('.confirmation-consequence');
    if (consequence) {
        consequenceDiv.innerHTML = `<i class="fas fa-info-circle me-2"></i>${consequence}`;
        consequenceDiv.style.display = 'block';
    } else {
        consequenceDiv.style.display = 'none';
    }
    
    // Set up confirm button
    const confirmBtn = modal.querySelector('#confirm-delete-btn');
    confirmBtn.onclick = function() {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
        onConfirm();
    };
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// ===== KEYBOARD SHORTCUTS =====
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('global-search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close search
        if (e.key === 'Escape') {
            hideSearchResults();
        }
    });
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initClickableStatusCards();
    initGlobalSearch();
    initActionDropdowns();
    initProgressiveDisclosure();
    initConfirmationDialogs();
    initKeyboardShortcuts();
    
    // Add smooth scrolling for all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
});

// Utility function for formatting dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString(undefined, options);
}

// Utility function for calculating days until
function daysUntil(dateString) {
    const target = new Date(dateString);
    const today = new Date();
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
}

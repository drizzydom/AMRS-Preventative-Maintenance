/**
 * HORIZONTAL SCROLL SUPPORT FOR MOUSE USERS
 * Adds mouse wheel horizontal scrolling support to table containers
 * and other scrollable elements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add horizontal scroll support for mouse wheels
    addHorizontalScrollSupport();
    
    // Add scroll indicators for better UX
    addScrollIndicators();
    
    // Add keyboard navigation support
    addKeyboardNavigation();
});

/**
 * Enable horizontal scrolling with mouse wheel (Shift + Wheel)
 * and provide visual feedback for scrollable content
 */
function addHorizontalScrollSupport() {
    const scrollableContainers = document.querySelectorAll('.table-responsive, .admin-table-container, .parts-table-container');
    
    scrollableContainers.forEach(container => {
        // Add mouse wheel horizontal scroll support
        container.addEventListener('wheel', function(e) {
            // Check if user is holding Shift key (common pattern for horizontal scroll)
            if (e.shiftKey) {
                e.preventDefault();
                container.scrollLeft += e.deltaY;
            }
        }, { passive: false });
        
        // Add CSS class for styling
        container.classList.add('horizontal-scrollable');
        
        // Add scroll position tracking
        container.addEventListener('scroll', function() {
            updateScrollIndicators(container);
        });
        
        // Initialize scroll indicators
        updateScrollIndicators(container);
    });
}

/**
 * Add visual indicators for horizontal scrolling
 */
function addScrollIndicators() {
    const scrollableContainers = document.querySelectorAll('.table-responsive, .admin-table-container, .parts-table-container');
    
    scrollableContainers.forEach(container => {
        // Create scroll indicator container
        const indicatorContainer = document.createElement('div');
        indicatorContainer.className = 'scroll-indicator-container';
        
        // Left scroll indicator
        const leftIndicator = document.createElement('div');
        leftIndicator.className = 'scroll-indicator scroll-indicator-left';
        leftIndicator.innerHTML = '<i class="fas fa-chevron-left"></i>';
        leftIndicator.title = 'Scroll left (Shift + Mouse Wheel)';
        
        // Right scroll indicator
        const rightIndicator = document.createElement('div');
        rightIndicator.className = 'scroll-indicator scroll-indicator-right';
        rightIndicator.innerHTML = '<i class="fas fa-chevron-right"></i>';
        rightIndicator.title = 'Scroll right (Shift + Mouse Wheel)';
        
        // Add click handlers for indicators
        leftIndicator.addEventListener('click', () => {
            container.scrollBy({ left: -200, behavior: 'smooth' });
        });
        
        rightIndicator.addEventListener('click', () => {
            container.scrollBy({ left: 200, behavior: 'smooth' });
        });
        
        indicatorContainer.appendChild(leftIndicator);
        indicatorContainer.appendChild(rightIndicator);
        
        // Insert indicator container before the scrollable container
        container.parentNode.insertBefore(indicatorContainer, container);
        
        // Store reference for updates
        container.scrollIndicators = {
            left: leftIndicator,
            right: rightIndicator
        };
    });
}

/**
 * Update scroll indicator visibility and opacity
 */
function updateScrollIndicators(container) {
    if (!container.scrollIndicators) return;
    
    const { left, right } = container.scrollIndicators;
    const scrollWidth = container.scrollWidth;
    const clientWidth = container.clientWidth;
    const scrollLeft = container.scrollLeft;
    
    // Show/hide indicators based on scroll position
    if (scrollWidth <= clientWidth) {
        // No scrolling needed
        left.style.display = 'none';
        right.style.display = 'none';
    } else {
        left.style.display = 'block';
        right.style.display = 'block';
        
        // Update opacity based on scroll position
        left.style.opacity = scrollLeft > 0 ? '1' : '0.3';
        right.style.opacity = scrollLeft < (scrollWidth - clientWidth) ? '1' : '0.3';
    }
}

/**
 * Add keyboard navigation support for better accessibility
 */
function addKeyboardNavigation() {
    const scrollableContainers = document.querySelectorAll('.table-responsive, .admin-table-container, .parts-table-container');
    
    scrollableContainers.forEach(container => {
        // Make container focusable
        container.setAttribute('tabindex', '0');
        
        // Add keyboard event listener
        container.addEventListener('keydown', function(e) {
            const scrollAmount = 100;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
                    break;
                case 'Home':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        container.scrollTo({ left: 0, behavior: 'smooth' });
                    }
                    break;
                case 'End':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        container.scrollTo({ left: container.scrollWidth, behavior: 'smooth' });
                    }
                    break;
            }
        });
        
        // Add focus/blur styling
        container.addEventListener('focus', function() {
            container.classList.add('scroll-focused');
        });
        
        container.addEventListener('blur', function() {
            container.classList.remove('scroll-focused');
        });
    });
}

/**
 * Initialize mouse wheel horizontal scrolling for any new content
 */
function initializeNewScrollableContent() {
    addHorizontalScrollSupport();
    addScrollIndicators();
    addKeyboardNavigation();
}

// Export for use in other scripts
window.horizontalScrollSupport = {
    init: initializeNewScrollableContent
};

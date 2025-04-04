/**
 * DIRECT ICON COLOR FIX
 * Uses JavaScript to force the icon color to match the others
 */
(function() {
    function fixPartIconColor() {
        // Target all possible elements that could be the Parts icon - extremely aggressive approach
        const iconSelectors = [
            '.col-md-3:nth-child(4) .card-body i', 
            '.col-md-3:nth-child(4) .card i',
            '.col-md-3:nth-child(4) .display-4 + a',
            '.col-md-3:nth-child(4) .card-body .fas',
            'a[href*="parts"] i', 
            '.card:has(h5:contains("Parts")) i',
            '.card:has(.card-title:contains("Parts")) i',
            '.card i.fa-cogs',
            '.card-body i.fa-cogs',
            '[class*="parts"] i',
            '.card-icon.bg-warning',
            '.card-icon.bg-primary',
            '.card-icon[style*="orange"]',
            '.card-icon[style*="warning"]',
            '.card-icon', // Generic fallback
            '.icon-container' // Generic fallback
        ];
        
        // Get all elements matching our selectors
        let partsIcons = [];
        iconSelectors.forEach(selector => {
            try {
                const matches = document.querySelectorAll(selector);
                if (matches.length) {
                    partsIcons = partsIcons.concat(Array.from(matches));
                }
            } catch (e) {
                // Some complex selectors might not be supported in all browsers
            }
        });
        
        // Direct target for the Parts card in Admin dashboard (most likely culprit)
        const adminCards = document.querySelectorAll('.row .col-md-3');
        if (adminCards.length >= 4) {
            const partsCard = adminCards[3]; // Fourth card (0-based index)
            if (partsCard) {
                const icons = partsCard.querySelectorAll('i, .fa, .fas, .card-icon, .icon-container');
                if (icons.length) {
                    partsIcons = partsIcons.concat(Array.from(icons));
                }
                
                // Also target the entire card to find any colored elements
                const coloredElements = Array.from(partsCard.querySelectorAll('*')).filter(el => {
                    const style = window.getComputedStyle(el);
                    return style.backgroundColor && 
                           (style.backgroundColor.includes('255, 152') || // Orange-ish colors
                            style.backgroundColor.includes('254, 121') ||
                            style.backgroundColor.includes('orange') ||
                            style.backgroundColor.includes('warning'));
                });
                
                partsIcons = partsIcons.concat(coloredElements);
            }
        }
        
        // Force the color using inline style with !important
        partsIcons.forEach(icon => {
            if (icon) {
                icon.style.cssText += '; background-color: #5E5E5E !important; color: white !important;';
                
                // Also set attributes that might be used for styling
                icon.setAttribute('data-fixed-color', 'true');
                
                // Remove any classes that might cause orange color
                icon.classList.remove('bg-warning', 'bg-primary', 'text-warning', 'text-orange');
                
                // Add our own class for consistency
                icon.classList.add('bg-secondary', 'icon-fixed');
            }
        });
    }
    
    // Run the fix immediately
    fixPartIconColor();
    
    // Then run it again after a short delay to catch any late-loaded elements
    setTimeout(fixPartIconColor, 500);
    
    // And set up a mutation observer to watch for changes
    if (window.MutationObserver) {
        const observer = new MutationObserver(fixPartIconColor);
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
})();

/**
 * Direct Text Fix - Immediate Text Removal
 * Uses the most aggressive possible technique to immediately remove the specific text
 */

// Execute immediately without waiting for DOMContentLoaded
(function() {
    // Function to directly find and eliminate the text
    function removeSpecificText() {
        // Direct text node removal using regex
        const allElements = document.body.getElementsByTagName('*');
        
        for (let i = 0; i < allElements.length; i++) {
            const element = allElements[i];
            
            // Check for text nodes that are direct children
            for (let j = 0; j < element.childNodes.length; j++) {
                const node = element.childNodes[j];
                
                // If it's a text node and contains our target text
                if (node.nodeType === 3 && 
                    node.nodeValue && 
                    (node.nodeValue.includes('Currently showing') || 
                     node.nodeValue.trim() === ':' ||
                     node.nodeValue.match(/^:[a-zA-Z0-9\s]+$/))) {
                    
                    // Remove the text completely
                    node.nodeValue = '';
                }
            }
            
            // Also check for possible ::before content
            if (element.classList && 
                (element.classList.contains('card-header') || 
                 element.classList.contains('d-flex') || 
                 element.classList.contains('site-filter-dropdown') || 
                 element.classList.contains('machine-filter-dropdown'))) {
                
                // Apply style to remove any ::before pseudo element
                element.style.setProperty('--filter-prefix', 'none', 'important');
                element.style.setProperty('content', 'none', 'important');
                
                // Also check for data attributes that might be used for content
                element.removeAttribute('data-content');
                element.removeAttribute('data-before');
                element.removeAttribute('data-label');
            }
        }
    }
    
    // Run immediately
    removeSpecificText();
    
    // Then run again after a very short delay to catch any elements 
    // that might have been created after the initial script execution
    setTimeout(removeSpecificText, 10);
    setTimeout(removeSpecificText, 100);
    setTimeout(removeSpecificText, 500);
    
    // Continuously monitor for 5 seconds to ensure complete removal
    let checkCount = 0;
    const interval = setInterval(function() {
        removeSpecificText();
        checkCount++;
        if (checkCount >= 50) clearInterval(interval); // Stop after 5 seconds (50 * 100ms)
    }, 100);
    
    // Create a MutationObserver to watch for any DOM changes
    if (window.MutationObserver) {
        const observer = new MutationObserver(removeSpecificText);
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true
        });
    }
})();

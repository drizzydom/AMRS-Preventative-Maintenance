/**
 * CARD HEADER TEXT ELIMINATOR
 * Completely rebuilds card headers to ensure no unwanted text can exist
 */

// Self-executing function that runs immediately when the file loads
(function() {
    // Function to completely rebuild card headers
    function rebuildCardHeaders() {
        // Target all card headers
        const cardHeaders = document.querySelectorAll('.card-header');
        
        cardHeaders.forEach(function(header) {
            // First, save important elements
            const title = header.querySelector('.card-title, h5');
            const select = header.querySelector('select, .form-select');
            const buttons = Array.from(header.querySelectorAll('.btn'));
            
            if (select) {
                // Create a clean container with no text nodes
                const cleanContainer = document.createElement('div');
                cleanContainer.className = 'card-header-clean';
                cleanContainer.style.cssText = 'display:flex;justify-content:space-between;align-items:center;width:100%;padding:0;';
                
                // Create left side with title
                const leftSide = document.createElement('div');
                leftSide.style.cssText = 'flex:1;';
                
                // Create right side with controls
                const rightSide = document.createElement('div');
                rightSide.style.cssText = 'text-align:right;font-size:0;'; // font-size:0 prevents any text nodes
                
                // Add title to left side
                if (title) {
                    leftSide.appendChild(title.cloneNode(true));
                }
                
                // Add select to right side
                rightSide.appendChild(select.cloneNode(true));
                
                // Add buttons to right side
                buttons.forEach(function(button) {
                    const newButton = button.cloneNode(true);
                    newButton.style.marginLeft = '0.5rem';
                    rightSide.appendChild(newButton);
                });
                
                // Add sides to container
                cleanContainer.appendChild(leftSide);
                cleanContainer.appendChild(rightSide);
                
                // Replace entire card header content
                header.innerHTML = '';
                header.appendChild(cleanContainer);
            }
        });
        
        // Ensure all select elements have their event handlers and values preserved
        document.querySelectorAll('.card-header select').forEach(function(select) {
            const originalId = select.id;
            if (originalId) {
                const originalSelect = document.getElementById(originalId + '_original');
                if (originalSelect) {
                    // Copy value from original
                    select.value = originalSelect.value;
                    
                    // Copy onchange handler
                    if (originalSelect.getAttribute('onchange')) {
                        select.setAttribute('onchange', originalSelect.getAttribute('onchange'));
                    }
                }
            }
        });
    }
    
    // Function to ensure there are no text nodes in critical areas
    function removeTextNodes() {
        // Get all card headers and their children
        const cardHeaderElements = document.querySelectorAll('.card-header, .card-header *, .card-header-clean, .card-header-clean *');
        
        cardHeaderElements.forEach(function(element) {
            // Check for unwanted direct text nodes
            for (let i = 0; i < element.childNodes.length; i++) {
                const node = element.childNodes[i];
                if (node.nodeType === 3) { // Text node
                    element.removeChild(node);
                    i--; // Adjust index since we removed a node
                }
            }
        });
    }
    
    // Run immediately
    rebuildCardHeaders();
    removeTextNodes();
    
    // Run again after a short delay to catch any dynamic changes
    setTimeout(function() {
        rebuildCardHeaders();
        removeTextNodes();
        
        // Set up a MutationObserver to watch for changes
        const observer = new MutationObserver(function(mutations) {
            removeTextNodes();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }, 10);
    
    // Add a smaller, more focused interval for continuous monitoring
    setInterval(removeTextNodes, 250);
})();

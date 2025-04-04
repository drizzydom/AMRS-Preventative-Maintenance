/**
 * Text Node Fix - Nuclear Edition
 * Aggressively removes all unwanted text nodes from the DOM
 */

document.addEventListener('DOMContentLoaded', function() {
    // More aggressive function to remove unwanted text
    function nukeUnwantedText() {
        // First, try to directly target the parent containing "Currently showing" text
        const cardHeaders = document.querySelectorAll('.card-header');
        
        cardHeaders.forEach(header => {
            // Check all direct text nodes
            Array.from(header.childNodes).forEach(node => {
                if (node.nodeType === 3) { // Text node
                    node.textContent = ''; // Empty it
                }
            });
            
            // Check the d-flex container
            const flexContainers = header.querySelectorAll('.d-flex');
            flexContainers.forEach(container => {
                Array.from(container.childNodes).forEach(node => {
                    if (node.nodeType === 3) { // Text node
                        node.textContent = ''; // Empty it
                    }
                });
            });
            
            // Target specific wrapper elements that might contain text
            const filterContainers = header.querySelectorAll('[class*="filter"], [class*="dropdown"]');
            filterContainers.forEach(container => {
                Array.from(container.childNodes).forEach(node => {
                    if (node.nodeType === 3) { // Text node
                        node.textContent = ''; // Empty it
                    }
                });
            });
        });
        
        // Fallback: Use a more general approach for any remaining text
        const textFinder = new RegExp('Currently showing|All sites|All machines', 'i');
        const treeWalker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            { acceptNode: node => textFinder.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT },
            false
        );
        
        const nodesToRemove = [];
        let currentNode;
        
        while (currentNode = treeWalker.nextNode()) {
            nodesToRemove.push(currentNode);
        }
        
        nodesToRemove.forEach(node => {
            if (node.parentNode) {
                node.nodeValue = '';
            }
        });
    }
    
    // Run immediately
    nukeUnwantedText();
    
    // Run periodically to catch anything that might be added dynamically
    setInterval(nukeUnwantedText, 200);
    
    // Also observe DOM changes
    const observer = new MutationObserver(nukeUnwantedText);
    observer.observe(document.body, { 
        childList: true, 
        subtree: true,
        characterData: true,
        characterDataOldValue: true
    });
});

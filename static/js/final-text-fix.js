/**
 * Ultimate Text Node Fix
 * The most aggressive possible solution to eliminate unwanted text nodes
 */

// Execute immediately without waiting for DOMContentLoaded
(function() {
    // Function to completely eliminate all text nodes in card headers
    function ultimateTextFix() {
        // Target tables in card headers specifically
        const cardHeaderTables = document.querySelectorAll('.card-header table');
        
        cardHeaderTables.forEach(table => {
            const cells = table.querySelectorAll('td');
            if (cells.length >= 2) {
                const rightCell = cells[1]; // Right cell with filter
                
                // First, clone the select elements to preserve them
                const selects = Array.from(rightCell.querySelectorAll('select, .form-select'));
                const buttons = Array.from(rightCell.querySelectorAll('.btn, button'));
                
                // Save their current values and event handlers
                const selectData = selects.map(select => ({
                    element: select,
                    value: select.value,
                    parent: select.parentNode,
                    nextSibling: select.nextSibling,
                    attributes: Array.from(select.attributes).map(attr => ({
                        name: attr.name,
                        value: attr.value
                    })),
                    html: select.outerHTML
                }));
                
                const buttonData = buttons.map(button => ({
                    element: button,
                    parent: button.parentNode,
                    nextSibling: button.nextSibling,
                    attributes: Array.from(button.attributes).map(attr => ({
                        name: attr.name,
                        value: attr.value
                    })),
                    html: button.outerHTML
                }));
                
                // Clear the cell completely
                rightCell.innerHTML = '';
                
                // Now restore only the essential elements in a clean container
                const cleanContainer = document.createElement('div');
                cleanContainer.style.textAlign = 'right';
                cleanContainer.style.display = 'flex';
                cleanContainer.style.justifyContent = 'flex-end';
                cleanContainer.style.alignItems = 'center';
                
                // Restore selects
                selectData.forEach(data => {
                    // Create a new clean select
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = data.html;
                    const newSelect = tempDiv.firstChild;
                    
                    // Set all attributes
                    data.attributes.forEach(attr => {
                        if (attr.name !== 'style') { // Skip style which might contain problematic values
                            newSelect.setAttribute(attr.name, attr.value);
                        }
                    });
                    
                    // Restore value
                    newSelect.value = data.value;
                    
                    // Add to clean container
                    cleanContainer.appendChild(newSelect);
                });
                
                // Restore buttons with a margin
                buttonData.forEach(data => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = data.html;
                    const newButton = tempDiv.firstChild;
                    
                    // Set all attributes
                    data.attributes.forEach(attr => {
                        if (attr.name !== 'style') {
                            newButton.setAttribute(attr.name, attr.value);
                        }
                    });
                    
                    // Add margin for spacing
                    newButton.style.marginLeft = '0.5rem';
                    
                    // Add to clean container
                    cleanContainer.appendChild(newButton);
                });
                
                // Add the clean container back to the cell
                rightCell.appendChild(cleanContainer);
            }
        });
        
        // Also handle non-table card headers (backup approach)
        const cardHeaders = document.querySelectorAll('.card-header:not(:has(table))');
        
        cardHeaders.forEach(header => {
            // Find all text nodes directly under the card header
            const walker = document.createTreeWalker(
                header,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                // If the text node contains actual text (not just whitespace)
                if (node.nodeValue.trim()) {
                    textNodes.push(node);
                }
            }
            
            // Remove all found text nodes
            textNodes.forEach(node => {
                if (node.parentNode) {
                    node.nodeValue = '';
                }
            });
        });
    }
    
    // Function to run after a brief delay to ensure elements are loaded
    function runFix() {
        ultimateTextFix();
        
        // Also set a mutation observer to catch dynamic changes
        const observer = new MutationObserver(function(mutations) {
            ultimateTextFix();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
        
        // Run periodically for extra safety
        setInterval(ultimateTextFix, 500);
    }
    
    // If the document is already loaded, run now
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(runFix, 1);
    } else {
        // Otherwise wait for it to load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(runFix, 1);
        });
    }
    
    // Also run immediately in case the document is already partially loaded
    setTimeout(ultimateTextFix, 1);
})();

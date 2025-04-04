/**
 * Simple Text Fix
 * A lightweight, non-intensive solution to remove unwanted text
 */

document.addEventListener('DOMContentLoaded', function() {
    // Target specific areas where unwanted text appears
    const cardHeaders = document.querySelectorAll('.card-header');
    
    cardHeaders.forEach(function(header) {
        // Process direct text nodes
        Array.from(header.childNodes).forEach(function(node) {
            if (node.nodeType === 3 && node.nodeValue && node.nodeValue.trim()) {
                node.nodeValue = '';
            }
        });
        
        // Clean d-flex containers that might have text
        const flexContainers = header.querySelectorAll('.d-flex');
        flexContainers.forEach(function(container) {
            Array.from(container.childNodes).forEach(function(node) {
                if (node.nodeType === 3 && node.nodeValue && node.nodeValue.trim()) {
                    node.nodeValue = '';
                }
            });
        });
    });
});

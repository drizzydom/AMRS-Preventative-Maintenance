/**
 * AJAX Page Loader
 * 
 * This script handles partial page loading via AJAX to improve
 * the performance of page navigation without full page reloads.
 */

class AjaxLoader {
    constructor() {
        // Cache of loaded pages
        this.pageCache = {};
        
        // Element where content will be loaded
        this.contentContainer = document.querySelector('.content-container');
        
        // The main content zone of the page
        this.mainContent = document.querySelector('.main-content');
        
        // Element for page title
        this.pageTitleElement = document.querySelector('.page-title');
        
        // Current page URL
        this.currentUrl = window.location.pathname;
        
        // Loading indicator
        this.loadingIndicator = this.createLoadingIndicator();
        document.body.appendChild(this.loadingIndicator);
        
        // Initialize
        this.init();
    }
    
    // Create a loading spinner
    createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('ajax-loading-indicator');
        indicator.innerHTML = `
            <div class="spinner">
                <i class="fas fa-spinner fa-spin"></i>
            </div>
        `;
        indicator.style.display = 'none';
        
        // Add CSS for the loading indicator
        const style = document.createElement('style');
        style.textContent = `
            .ajax-loading-indicator {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.7);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            html[data-theme="dark"] .ajax-loading-indicator {
                background: rgba(0, 0, 0, 0.7);
            }
            
            .ajax-loading-indicator .spinner {
                font-size: 3rem;
                color: #3498db;
            }
        `;
        document.head.appendChild(style);
        
        return indicator;
    }
    
    // Show loading indicator
    showLoading() {
        this.loadingIndicator.style.display = 'flex';
    }
    
    // Hide loading indicator
    hideLoading() {
        this.loadingIndicator.style.display = 'none';
    }
    
    // Initialize the AJAX loader
    init() {
        // Only intercept clicks inside the sidebar navigation
        const navLinks = document.querySelectorAll('.sidebar-nav a');
        
        navLinks.forEach(link => {
            link.addEventListener('click', event => {
                // Don't intercept external links or downloads
                if (link.getAttribute('href').startsWith('http') || 
                    link.hasAttribute('download') || 
                    link.getAttribute('target') === '_blank') {
                    return;
                }
                
                // Get the link URL
                const url = link.getAttribute('href');
                
                // Don't intercept hash links (same-page anchors)
                if (url.startsWith('#')) {
                    return;
                }
                
                // Handle the navigation
                event.preventDefault();
                this.loadPage(url);
                
                // Handle mobile navigation - close sidebar after clicking
                if (window.innerWidth < 992) {
                    document.body.classList.remove('sidebar-open');
                }
                
                // Update the active state in the navigation
                this.updateActiveNavItem(link);
            });
        });
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', event => {
            if (event.state && event.state.url) {
                this.loadPage(event.state.url, false);
            }
        });
        
        // Save initial state
        history.replaceState({ url: window.location.pathname }, '', window.location.pathname);
    }
    
    // Update the active navigation item
    updateActiveNavItem(activeLink) {
        // Remove active class from all links
        document.querySelectorAll('.sidebar-nav a').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to the clicked link
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }
    
    // Update the page title
    updatePageTitle(newContent) {
        // Extract title from the loaded content
        const titleMatch = newContent.match(/<title>(.*?)<\/title>/i);
        if (titleMatch && titleMatch[1]) {
            document.title = titleMatch[1];
        }
        
        // Update the page header title if we can find it
        const headerTitleMatch = newContent.match(/<h1 class="page-title">(.*?)<\/h1>/i);
        if (headerTitleMatch && headerTitleMatch[1] && this.pageTitleElement) {
            this.pageTitleElement.innerHTML = headerTitleMatch[1];
        }
    }
    
    // Load page content via AJAX
    loadPage(url, updateHistory = true) {
        // Show loading indicator
        this.showLoading();
        
        // Check if page is in cache
        if (this.pageCache[url]) {
            this.updateContent(this.pageCache[url], url, updateHistory);
            this.hideLoading();
            return;
        }
        
        // Fetch the page
        fetch(url, { 
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            // Cache the response
            this.pageCache[url] = html;
            
            // Update the page content
            this.updateContent(html, url, updateHistory);
        })
        .catch(error => {
            console.error('Error loading page:', error);
            // On error, redirect to the page instead
            window.location.href = url;
        })
        .finally(() => {
            // Hide loading indicator
            this.hideLoading();
        });
    }
    
    // Update the page content with the loaded HTML
    updateContent(html, url, updateHistory) {
        try {
            // Create a temporary element to hold the loaded content
            const temp = document.createElement('div');
            temp.innerHTML = html;
            
            // Extract just the content container
            const newContent = temp.querySelector('.content-container');
            if (!newContent) {
                // If we can't find the content container, redirect to the page
                window.location.href = url;
                return;
            }
            
            // Update the page title
            this.updatePageTitle(html);
            
            // Update the content
            this.contentContainer.innerHTML = newContent.innerHTML;
            
            // Execute any scripts in the new content
            this.executeScripts(newContent);
            
            // Update browser history
            if (updateHistory) {
                history.pushState({ url }, '', url);
            }
            
            // Scroll to top
            this.mainContent.scrollTo(0, 0);
            
            // Update current URL
            this.currentUrl = url;
            
            // Find the correct nav link and mark it active
            const activeNavLink = document.querySelector(`.sidebar-nav a[href="${url}"]`);
            if (activeNavLink) {
                this.updateActiveNavItem(activeNavLink);
            }
        } catch (error) {
            console.error('Error updating content:', error);
            // On error, redirect to the page
            window.location.href = url;
        }
    }
    
    // Execute scripts in the new content
    executeScripts(container) {
        // Find all script tags
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            // Create a new script element
            const newScript = document.createElement('script');
            
            // Copy all attributes
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            
            // Copy the content
            newScript.innerHTML = oldScript.innerHTML;
            
            // Replace the old script with the new one
            if (oldScript.parentNode) {
                oldScript.parentNode.replaceChild(newScript, oldScript);
            } else {
                // If there's no parent, just append to the body
                document.body.appendChild(newScript);
            }
        });
    }
}

// Initialize the AJAX loader when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ajaxLoader = new AjaxLoader();
});

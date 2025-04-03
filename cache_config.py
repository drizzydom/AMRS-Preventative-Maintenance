from flask import Flask
from datetime import timedelta

def configure_caching(app):
    """Configure caching for static files to improve performance"""
    
    # Set cache duration for different asset types
    cache_timeouts = {
        'SEND_FILE_MAX_AGE_DEFAULT': timedelta(days=1),
        'static/css': timedelta(days=30),  # Cache CSS files for 30 days
        'static/js': timedelta(days=30),   # Cache JS files for 30 days
        'static/img': timedelta(days=30),  # Cache images for 30 days
        'static/fonts': timedelta(days=30) # Cache fonts for 30 days
    }
    
    # Apply cache settings to app
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = cache_timeouts['SEND_FILE_MAX_AGE_DEFAULT']
    
    # Function to be called by Flask for static files
    @app.after_request
    def add_cache_headers(response):
        # Only add caching headers to static files
        if request_is_for_static_file(response):
            path = request.path
            # Determine which max-age to use based on file type
            max_age = None
            for folder, timeout in cache_timeouts.items():
                if folder != 'SEND_FILE_MAX_AGE_DEFAULT' and folder in path:
                    max_age = int(timeout.total_seconds())
                    break
            
            # If no specific rule, use default
            if max_age is None:
                max_age = int(cache_timeouts['SEND_FILE_MAX_AGE_DEFAULT'].total_seconds())
            
            # Set cache control header
            response.cache_control.public = True
            response.cache_control.max_age = max_age
            
            # Add expires header
            response.expires = int(max_age)
        
        return response
    
    def request_is_for_static_file(response):
        """Check if the response is for a static file"""
        if not hasattr(request, 'path'):
            return False
        
        path = request.path
        # Check if path is for a static file
        static_extensions = ('.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf')
        return any(path.endswith(ext) for ext in static_extensions)

    # Import request module here to avoid circular import
    from flask import request

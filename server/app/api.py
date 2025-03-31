# Change this:
def get_user_data():
    # ...existing code...
    response = {
        'user': user_data,
        'profile_url': url_for('user_profile', _external=True)
    }
    
# To this:
def get_user_data():
    # ...existing code...
    response = {
        'user': user_data,
        # Either use an existing endpoint:
        'profile_url': url_for('user_details', _external=True)
        # Or just construct the URL directly:
        # 'profile_url': f"{request.url_root.rstrip('/')}/api/user/details"
    }
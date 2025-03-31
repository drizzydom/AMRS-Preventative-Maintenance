from app import create_app

# Create the application instance
app = create_app()

# Main entry point for direct execution
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000, debug=True)

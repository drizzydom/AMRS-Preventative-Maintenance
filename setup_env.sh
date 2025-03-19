#!/bin/bash

# Check if Python 3.11 is installed
python3.11 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Python 3.11 is not installed. Please install it before continuing."
    echo "You can install it with Homebrew: brew install python@3.11"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat > .env << EOL
# Email Configuration
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=password
MAIL_DEFAULT_SENDER=maintenance@example.com
EOL
    echo "Created .env file. Please update with your actual email configuration"
fi

echo ""
echo "Setup complete! You can now run the application with:"
echo "source venv/bin/activate && python app.py"

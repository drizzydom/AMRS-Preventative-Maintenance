#!/bin/bash

# First check if venv exists but might be broken (pointing to old location)
if [ -d "venv" ]; then
    # Check if it's pointing to the old location
    if grep -q "Copilot Preventative Maintenance" venv/bin/activate 2>/dev/null; then
        echo "Found virtual environment pointing to old repository location."
        echo "Removing old virtual environment..."
        rm -rf venv
        echo "Old virtual environment removed."
    fi
fi

# Check Python version - try 3.11 first, fallback to 3.10 or 3.9
python_cmd=""
for version in "python3.11" "python3.10" "python3.9" "python3"; do
    if command -v $version &> /dev/null; then
        python_cmd=$version
        echo "Using $python_cmd"
        break
    fi
done

if [ -z "$python_cmd" ]; then
    echo "Error: Could not find Python 3.9 or newer. Please install Python 3.9+ before continuing."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with $python_cmd..."
    $python_cmd -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error creating virtual environment. Please ensure you have the venv module installed."
        echo "You can install it with: $python_cmd -m pip install --user virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're using the correct Python from the new venv
echo "Using Python at: $(which python)"

# Install or upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error installing required packages. Check your requirements.txt file."
    exit 1
fi

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

# Ensure templates directory exists
python -c "
import os
basedir = os.path.abspath(os.path.dirname('$0'))
templates_dir = os.path.join(basedir, 'templates')
email_dir = os.path.join(templates_dir, 'email')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
    print(f'Created templates directory: {templates_dir}')
if not os.path.exists(email_dir):
    os.makedirs(email_dir)
    print(f'Created email templates directory: {email_dir}')
"

echo ""
echo "Setup complete! You can now run the application with:"
echo "./run.sh"
echo "or"
echo "source venv/bin/activate && python app.py"

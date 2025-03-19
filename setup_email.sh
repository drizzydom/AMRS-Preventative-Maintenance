#!/bin/bash

# Create a backup of the current .env file if it exists
if [ -f ".env" ]; then
    cp .env .env.backup
    echo "Created backup of current .env file as .env.backup"
fi

echo "Setting up email configuration..."
echo "Please provide your email server details:"

read -p "Mail Server (e.g., smtp.gmail.com): " mail_server
read -p "Mail Port (e.g., 587): " mail_port
read -p "Use TLS? (True/False): " mail_use_tls
read -p "Mail Username: " mail_username
read -p "Mail Password: " mail_password
read -p "Default Sender Email: " mail_sender

# Create or update the .env file
cat > .env << EOL
# Email Configuration
MAIL_SERVER=${mail_server:-smtp.example.com}
MAIL_PORT=${mail_port:-587}
MAIL_USE_TLS=${mail_use_tls:-True}
MAIL_USERNAME=${mail_username:-user@example.com}
MAIL_PASSWORD=${mail_password:-password}
MAIL_DEFAULT_SENDER=${mail_sender:-maintenance@example.com}
EOL

echo "Email configuration updated successfully!"
echo "You can test your email configuration by going to /admin/test-email in the app."

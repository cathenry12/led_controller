#!/bin/bash

# Exit on error
set -e

# Get the directory where this script is located
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Detected install directory: $APP_DIR"

echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libbluetooth-dev

echo "Installing Python requirements..."
# Try installing with --break-system-packages (for Bookworm) or fall back to normal
# We use sudo -H to ensure it installs for root usage (needed for service)
if ! sudo -H pip3 install -r "$APP_DIR/requirements.txt" --break-system-packages; then
    echo "Retrying without break-system-packages..."
    sudo -H pip3 install -r "$APP_DIR/requirements.txt"
fi

echo "Configuring systemd service..."
# Update the service file with the actual directory path
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$APP_DIR|g" "$APP_DIR/led-controller.service"
sed -i "s|ExecStart=.*|ExecStart=/usr/bin/python3 $APP_DIR/led_controller.py|g" "$APP_DIR/led-controller.service"

echo "Setting up systemd service..."
sudo cp "$APP_DIR/led-controller.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-controller.service
sudo systemctl restart led-controller.service

echo "Installation complete! Service started."
echo "Check status with: systemctl status led-controller"

#!/bin/bash

# Exit on error
set -e

APP_DIR="/home/pi/led_controller"

echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libbluetooth-dev

echo "Installing Python requirements..."
# --break-system-packages is needed on newer Pi OS (Bookworm)
sudo pip3 install -r $APP_DIR/requirements.txt --break-system-packages || sudo pip3 install -r $APP_DIR/requirements.txt

echo "Setting up systemd service..."
sudo cp $APP_DIR/led-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable led-controller.service
sudo systemctl start led-controller.service

echo "Installation complete! Service started."
echo "Check status with: systemctl status led-controller"

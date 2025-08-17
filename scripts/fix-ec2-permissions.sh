#!/bin/bash
# Fix permissions on EC2 after deployment

echo "Fixing database permissions on EC2..."

# The appuser in Docker has UID 999
sudo chown -R 999:999 /home/ubuntu/liap-tui-data

echo "Permissions fixed! The application should now be able to write to the database."
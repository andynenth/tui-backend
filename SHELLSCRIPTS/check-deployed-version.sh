#!/bin/bash
# Check what version is actually deployed on EC2

echo "🔍 Checking deployed version on EC2..."

ssh -i ~/.ssh/liap-tui-key-1755152170.pem ubuntu@34.233.7.20 << 'EOF'
  echo -e "\n📦 Docker images:"
  sudo docker images | grep liap-tui | head -5

  echo -e "\n🏃 Running containers:"
  sudo docker-compose ps

  echo -e "\n🔎 Checking bundle.js version inside container:"
  # Get the container name
  CONTAINER=$(sudo docker-compose ps -q backend)
  if [ ! -z "$CONTAINER" ]; then
    echo "Container ID: $CONTAINER"

    # Check if bundle.js exists and its size
    echo -e "\n📁 Bundle.js info:"
    sudo docker exec $CONTAINER ls -la /app/backend/static/bundle.js 2>/dev/null || echo "bundle.js not found!"

    # Extract version from bundle
    echo -e "\n📌 Version in bundle.js:"
    sudo docker exec $CONTAINER grep -o '"1\.5\.[0-9]"' /app/backend/static/bundle.js 2>/dev/null | head -1 || echo "Version not found in bundle!"

    # Check VERSION file
    echo -e "\n📋 VERSION file:"
    sudo docker exec $CONTAINER cat /app/VERSION 2>/dev/null || echo "VERSION file not found!"
  else
    echo "❌ Backend container not running!"
  fi

  echo -e "\n🌐 Testing live endpoints:"
  echo "API Health:"
  curl -s https://castellan.andynenth.dev/api/health | grep -o '"version":"[^"]*"' || echo "Failed to get API version"

  echo -e "\n🔄 Last Docker pull time:"
  stat /home/ubuntu/liap-tui/.env | grep Modify || echo "Cannot determine last pull time"
EOF

echo -e "\n✅ Check complete!"

#!/bin/bash

# EC2 Deployment Script
# Ensures EC2 renders exactly like ./start.sh

echo "🚀 Building Liap Tui for EC2 deployment..."

# 1. Build frontend with CSS processing and minification (matches ./start.sh)
echo "📦 Building frontend with CSS processing..."
cd frontend
npm run build:docker
cd ..

# 2. Build Docker image
echo "🐳 Building Docker image..."
docker build -t liap-tui .

# 3. Test locally first
echo "🧪 Testing locally on port 5050..."
echo "Visit http://localhost:5050 to verify rendering matches ./start.sh"
docker run -d -p 5050:5050 --name liap-tui-test liap-tui

echo "✅ Build complete!"
echo ""
echo "To stop test container: docker stop liap-tui-test && docker rm liap-tui-test"
echo ""
echo "Next steps for EC2:"
echo "1. Tag image: docker tag liap-tui:latest your-ecr-repo/liap-tui:latest"
echo "2. Push to ECR: docker push your-ecr-repo/liap-tui:latest"
echo "3. Deploy to EC2 using your preferred method"
#!/bin/bash

echo "🚀 Starting Enterprise IT Copilot Deployment..."

# Ensure executable permissions
chmod +x deploy.sh

# Build the Docker image
echo "📦 Building Docker Image..."
docker build -t enterprise-copilot:latest .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully."
    
    # Run the container (mapping port 5000 for Flask)
    echo "🌐 Starting Container..."
    docker run -d -p 5000:5000 --name it-copilot enterprise-copilot:latest
    
    echo "🎉 Deployment Complete!"
    echo "Flask API and Copilot UI running on: http://localhost:5000"
else
    echo "❌ Docker build failed. Please check the logs."
    exit 1
fi

#!/bin/bash
# Build script for aareguru-mcp Docker image

set -e

echo "Building aareguru-mcp Docker image..."
docker build -t aareguru-mcp:latest .

echo ""
echo "Build complete!"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 aareguru-mcp:latest"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up"

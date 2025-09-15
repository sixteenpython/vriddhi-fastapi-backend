#!/bin/bash
# Build script for Render deployment

echo "🚀 Starting Render build process..."

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements-minimal.txt

echo "✅ Build completed successfully!"
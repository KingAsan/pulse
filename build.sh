#!/bin/bash
# Build script for Railway deployment

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Copy built frontend to backend static folder
rm -rf backend/static/*
cp -r frontend/dist/* backend/static/

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"

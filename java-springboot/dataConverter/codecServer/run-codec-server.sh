#!/bin/bash

# Temporal Remote Codec Server Startup Script
# This script builds and runs the Temporal remote codec server

set -e

echo "🚀 Starting Temporal Remote Codec Server..."

# Check if we're in the right directory
if [ ! -f "build.gradle" ]; then
    echo "❌ Error: build.gradle not found. Please run this script from the codecServer directory."
    exit 1
fi

# Build the project
echo "🔨 Building the codec server..."
../../gradlew build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed!"
    exit 1
fi

# Run the server
echo "🏃 Starting the codec server on port 8090..."
echo "📝 Logs will be displayed below. Press Ctrl+C to stop the server."
echo "🌐 Health check: http://localhost:8090/health"
echo "📊 Actuator endpoints: http://localhost:8090/actuator"
echo ""

../../gradlew bootRun

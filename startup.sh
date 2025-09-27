#!/bin/bash
# run_local.sh - Script to run the FastAPI app locally

echo "Setting up local development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables for local development
export APPLICATIONINSIGHTS_CONNECTION_STRING=""
export ENVIRONMENT="development"
export PORT=8000

echo "Starting FastAPI application locally..."
echo "Application will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
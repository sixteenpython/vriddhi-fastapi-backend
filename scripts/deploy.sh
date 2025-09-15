#!/bin/bash

# Vriddhi FastAPI Backend Deployment Script
# This script handles deployment to Railway and other platforms

set -e  # Exit on any error

echo "🚀 Vriddhi FastAPI Backend Deployment Script"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI is not installed. Please install it first:"
        echo "npm install -g @railway/cli"
        echo "or visit: https://railway.app/cli"
        exit 1
    fi
}

# Check if logged into Railway
check_railway_login() {
    if ! railway whoami &> /dev/null; then
        print_error "Not logged into Railway. Please login first:"
        echo "railway login"
        exit 1
    fi
}

# Validate environment
validate_environment() {
    print_status "Validating environment..."

    # Check Python version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $python_version"

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi

    # Check if main application exists
    if [ ! -f "app/main.py" ]; then
        print_error "app/main.py not found!"
        exit 1
    fi

    print_success "Environment validation passed"
}

# Build and test locally
local_test() {
    print_status "Running local tests..."

    # Install dependencies
    pip install -r requirements.txt

    # Run basic import test
    python -c "from app.main import app; print('✅ App imports successfully')"

    print_success "Local tests passed"
}

# Deploy to Railway
deploy_to_railway() {
    print_status "Deploying to Railway..."

    # Check if project exists or needs to be created
    if ! railway status &> /dev/null; then
        print_status "Creating new Railway project..."
        railway login
        railway init
    fi

    # Add PostgreSQL if not exists
    print_status "Ensuring PostgreSQL service exists..."
    railway add --database postgresql || true

    # Set environment variables
    print_status "Setting environment variables..."
    railway variables set ENVIRONMENT=production
    railway variables set PYTHONPATH=/app
    railway variables set LOG_LEVEL=INFO
    railway variables set DEFAULT_EXPECTED_CAGR=0.15
    railway variables set MIN_MONTHLY_INVESTMENT=50000

    # Deploy
    print_status "Starting deployment..."
    railway deploy

    # Get deployment URL
    deployment_url=$(railway url 2>/dev/null || echo "URL not available yet")

    print_success "Deployment initiated!"
    print_status "Deployment URL: $deployment_url"
}

# Setup database and run migration
setup_database() {
    print_status "Setting up database..."

    # Copy CSV file to deployment if exists
    if [ -f "../vriddhi-core/grand_table_expanded.csv" ]; then
        print_status "Copying stock data..."
        cp "../vriddhi-core/grand_table_expanded.csv" "./data/" 2>/dev/null || true
    fi

    # Run migration (this would be done via Railway service or manual trigger)
    print_status "Database migration will be handled by the deployment process"
    print_warning "Remember to run the migration script after deployment:"
    echo "railway run python scripts/migrate_csv_to_db.py"
}

# Monitor deployment
monitor_deployment() {
    print_status "Monitoring deployment status..."

    # Show deployment logs
    print_status "Fetching deployment logs..."
    railway logs --follow &
    LOGS_PID=$!

    # Wait a bit then kill log follow
    sleep 10
    kill $LOGS_PID 2>/dev/null || true

    # Check health
    print_status "Checking application health..."
    sleep 5

    deployment_url=$(railway url 2>/dev/null || echo "")
    if [ -n "$deployment_url" ]; then
        health_url="$deployment_url/health"
        echo "Health check URL: $health_url"

        # Try health check (may fail if deployment is still starting)
        curl -s "$health_url" || print_warning "Health check failed - deployment may still be starting"
    fi
}

# Main deployment process
main() {
    echo "Starting deployment process..."
    echo "Deployment target: ${1:-railway}"

    case "${1:-railway}" in
        "railway")
            check_railway_cli
            check_railway_login
            validate_environment
            local_test
            setup_database
            deploy_to_railway
            monitor_deployment
            ;;
        "docker")
            print_status "Building Docker image..."
            docker build -t vriddhi-api .
            print_success "Docker image built successfully"
            print_status "To run locally: docker-compose up"
            ;;
        "local")
            validate_environment
            local_test
            print_status "Starting local development server..."
            python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
            ;;
        *)
            print_error "Unknown deployment target: $1"
            echo "Usage: $0 [railway|docker|local]"
            exit 1
            ;;
    esac

    print_success "Deployment process completed!"

    # Final instructions
    echo ""
    echo "🎉 Vriddhi API Deployment Complete!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Verify the deployment is healthy"
    echo "2. Run database migration if needed"
    echo "3. Test the API endpoints"
    echo "4. Update frontend configuration with the new API URL"
    echo ""
    echo "API Documentation: [deployment-url]/docs"
    echo "Health Check: [deployment-url]/health"
    echo ""
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
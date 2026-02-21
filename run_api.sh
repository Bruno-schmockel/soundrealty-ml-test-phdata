#!/bin/bash
# Run Sound Realty Prediction API with Gunicorn + Uvicorn Workers
# This script starts the FastAPI application in production mode

set -e  # Exit on error

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}Activating housing conda environment...${NC}"

# Activate the housing conda environment
# Note: Need to source conda.sh first for conda activate to work in bash scripts
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate housing

# Check if environment activated successfully
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate housing environment${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Sound Realty Prediction API...${NC}"
echo -e "${YELLOW}Server will be available at http://localhost:8000${NC}"
echo -e "${YELLOW}Interactive API docs at http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start Gunicorn with 4 Uvicorn workers
python -m gunicorn src.api.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

if [ $? -ne 0 ]; then
    echo -e "${RED}API server exited with error code: $?${NC}"
    exit 1
fi

echo -e "${YELLOW}API server stopped${NC}"

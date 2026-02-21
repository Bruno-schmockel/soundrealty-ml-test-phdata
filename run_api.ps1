# Run Sound Realty Prediction API with Gunicorn + Uvicorn Workers
# This script starts the FastAPI application in production mode

# Activate the housing conda environment
Write-Host "Activating housing conda environment..." -ForegroundColor Cyan
conda activate housing

# Check if environment activated successfully
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate housing environment" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Sound Realty Prediction API..." -ForegroundColor Green
Write-Host "Server will be available at http://localhost:8000" -ForegroundColor Yellow
Write-Host "Interactive API docs at http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Gunicorn with 4 Uvicorn workers
# Using python -m to handle Windows compatibility (Windows doesn't support fcntl module natively)
python -m gunicorn src.api.main:app `
    -w 4 `
    -k uvicorn.workers.UvicornWorker `
    --bind 0.0.0.0:8000 `
    --access-logfile - `
    --error-logfile - `
    --log-level info

if ($LASTEXITCODE -ne 0) {
    Write-Host "API server exited with error code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "API server stopped" -ForegroundColor Yellow

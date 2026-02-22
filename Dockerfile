# Build on Python 3.9 slim image
FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with compatible versions
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    fastapi \
    uvicorn[standard] \
    gunicorn \
    pydantic \
    matplotlib

# Copy application code
COPY src/ /app/src/
COPY model/ /app/model/
COPY data/ /app/data/
COPY gunicorn_config.py /app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application with Gunicorn (simple configuration for Docker)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "src.api.main:app"]

# Multi-stage build for efficient image size
FROM python:3.9-slim as builder

WORKDIR /app

# Install dependencies in a virtual environment
COPY env/conda_environment.yml .
RUN pip install --no-cache-dir conda-pack && \
    conda env create -f conda_environment.yml && \
    conda-pack -n housing -o /tmp/env.tar.gz && \
    mkdir /venv && cd /venv && tar xzf /tmp/env.tar.gz && \
    /venv/bin/python -m pip install --no-cache-dir gunicorn

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Copy application code
COPY src/ /app/src/
COPY model/ /app/model/
COPY data/ /app/data/
COPY gunicorn_config.py /app/

# Set environment variables
ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "src.api.main:app"]

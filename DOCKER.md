# Docker Setup and Usage Guide

## Overview

The Sound Realty Prediction API supports containerization using Docker for easy deployment and scaling. This guide covers building, running, and managing the containerized application.

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 1.29 or later)
- At least 2GB of available disk space
- At least 512MB of available memory

## Quick Start

### Using Docker Compose (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f soundrealty-api

# Stop the service
docker-compose down
```

The API will be available at `http://localhost:8000`

### Using Docker Directly

Build the image:
```bash
docker build -t soundrealty-api:latest .
```

Run the container:
```bash
docker run -d \
  --name soundrealty-api \
  -p 8000:8000 \
  -v $(pwd)/model:/app/model:ro \
  -v $(pwd)/data:/app/data:ro \
  soundrealty-api:latest
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available configuration options:
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `API_WORKERS`: Number of Gunicorn workers (default: 4)
- `LOG_LEVEL`: Logging level (default: INFO)

### Volume Mounts

The container uses read-only volumes for data:
- `./model:/app/model:ro` - Model artifacts (read-only)
- `./data:/app/data:ro` - Training data and demographics (read-only)

To update the model without rebuilding:
```bash
docker-compose restart soundrealty-api
```

## Health Checks

The container includes built-in health checks:

```bash
# Check container status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "demographics_loaded": true
}
```

## Testing

Run tests inside the container:

```bash
docker-compose exec soundrealty-api pytest src/tests/ -v
```

## Accessing the API

### From Host Machine

- Health Check: `curl http://localhost:8000/health`
- Predict Endpoint: `curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{...}'`
- Swagger Docs: `http://localhost:8000/docs`

### From Other Containers

If running other services on the same network:
```
http://soundrealty-api:8000
```

## Production Deployment

### Multi-Stage Build Benefits

The Dockerfile uses multi-stage builds to:
- Reduce final image size
- Improve security by excluding build dependencies
- Optimize layer caching

### Security Considerations

- Runs as non-root user (appuser)
- Uses read-only volumes for data
- Health checks ensure service availability
- Gunicorn configured for production

### Scaling

To run multiple API instances behind a load balancer:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  soundrealty-api:
    deploy:
      replicas: 3
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs soundrealty-api

# Check resources
docker stats soundrealty-api
```

### Health check failing
```bash
# Verify API is responding
docker-compose exec soundrealty-api curl http://localhost:8000/health

# Check logs for startup issues
docker-compose logs -f soundrealty-api
```

### High memory usage
Adjust Gunicorn workers in `.env`:
```
API_WORKERS=2
```

## Updating the Model

When you have a new trained model:

1. Replace `model/model.pkl` and `model/model_features.json`
2. Either:
   - Option A: Rebuild the image: `docker-compose build`
   - Option B: Restart container: `docker-compose restart soundrealty-api`
   - Option C: Use the `/reload-model` endpoint inside the container

## Monitoring

### Log Monitoring
```bash
# Follow logs in real-time
docker-compose logs -f soundrealty-api

# View last 100 lines
docker-compose logs --tail=100 soundrealty-api
```

### Resource Usage
```bash
# Monitor CPU and memory
docker stats soundrealty-api
```

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker-compose down --rmi all

# Clean up unused resources (careful!)
docker system prune -a
```

## Networking

By default, Docker Compose creates a bridge network `soundrealty-network`. Ensure port 8000 is available on your host.

### Custom Port Mapping

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Maps host port 8080 to container port 8000
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Configuration](https://gunicorn.org/)

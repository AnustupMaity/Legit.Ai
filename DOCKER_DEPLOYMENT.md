# Docker Deployment Guide

This guide explains how to deploy Legit.ai using Docker Compose for a one-command setup.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- (Optional) PostgreSQL and Redis if not using Docker services

## Quick Start

1. **Clone the repository and navigate to the project root**

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Services

The Docker Compose setup includes:

- **PostgreSQL**: Production-grade database
- **Redis**: For Celery task queue and caching
- **FastAPI Backend**: API server with ML capabilities
- **Celery Worker**: Background ML processing
- **React Frontend**: Web interface

## Configuration

Edit the `docker-compose.yml` file to customize:

- **Database credentials**: Change POSTGRES_USER and POSTGRES_PASSWORD
- **Ports**: Modify port mappings if needed
- **Environment variables**: Adjust API keys, model settings, etc.

## Production Deployment

For production deployment:

1. **Use production PostgreSQL instance**
   ```yaml
   environment:
     - DATABASE_URL=postgresql+asyncpg://user:password@production-host:5432/database
   ```

2. **Use external Redis**
   ```yaml
   environment:
     - CELERY_BROKER_URL=redis://production-redis:6379/0
   ```

3. **Set environment variables**
   ```bash
   export GEMINI_API_KEY=your_key
   export HF_TOKEN=your_token
   ```

4. **Use production-grade volumes**
   ```yaml
   volumes:
     - postgres_data:/var/lib/postgresql/data  # Use named volumes
   ```

## Scaling

To scale the Celery workers for higher throughput:

```bash
docker-compose up -d --scale celery_worker=4
```

## Monitoring

Check service status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f api
docker-compose logs -f celery_worker
```

## Troubleshooting

- **Database connection issues**: Ensure PostgreSQL is healthy before starting API
- **Model loading issues**: Check logs for Hugging Face download errors
- **Memory issues**: Reduce Celery worker concurrency or increase Docker memory limits

## Stopping Services

```bash
docker-compose down
```

To remove volumes (WARNING: deletes data):
```bash
docker-compose down -v
```

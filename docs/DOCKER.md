# Docker Configuration and Development

## Overview

This document outlines the Docker setup for the Support Bot project, providing instructions for local development, deployment strategies, and best practices.

## Local Development Environment

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your machine
- Git for version control
- Basic knowledge of Docker and containers

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/support-bot.git
   cd support-bot
   ```

2. **Setup environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit the .env file with your configuration
   # At minimum, set the SUPPORT_BOT_TOKEN
   ```

3. **Start the development environment**
   ```bash
   # On Windows
   .\dev.ps1 up
   
   # On macOS/Linux
   # Make the script executable first
   chmod +x ./dev.sh
   ./dev.sh up
   ```

## Docker Components

### Dockerfile

The project uses a multi-stage Dockerfile optimized for both development and production:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore

The `.dockerignore` file reduces build context size by excluding unnecessary files:

```
# Git
.git
.gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
...
```

This improves build performance and reduces image size by preventing irrelevant files from being copied into the Docker image.

### Docker Compose

The `docker-compose.yml` file configures the development environment:

```yaml
version: '3.8'

services:
  supportbot:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - SUPPORT_BOT_TOKEN=${SUPPORT_BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - MAX_CONNECTIONS=${MAX_CONNECTIONS:-20}
      - POOL_TIMEOUT=${POOL_TIMEOUT:-30}
      - ENVIRONMENT=development
    depends_on:
      - db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=supportbot
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Development Workflow

### Helper Scripts

The project includes PowerShell scripts (`dev.ps1`) to simplify common Docker operations:

| Command | Description |
|---------|-------------|
| `.\dev.ps1 up` | Start the development environment |
| `.\dev.ps1 down` | Stop the development environment |
| `.\dev.ps1 restart` | Restart services |
| `.\dev.ps1 logs` | Show logs |
| `.\dev.ps1 shell` | Open a shell in the container |
| `.\dev.ps1 test` | Run tests |

### Making Changes

The development workflow is designed for rapid iteration:

1. Make changes to the code
2. The application will automatically reload (thanks to `--reload` flag)
3. Test changes locally
4. When satisfied, commit and push to GitHub

## Deployment Strategies

### Railway Deployment

The project is configured for deployment on Railway:

1. **Current Flow**
   - Changes are pushed to GitHub
   - Railway detects changes and rebuilds the app
   - This can be resource-intensive for small changes

2. **Optimized Flow**
   - Develop and test locally using Docker
   - Push only stable changes to GitHub
   - Railway builds from the GitHub repository

### Improving Railway Builds

To optimize Railway builds:

1. **Use Build Cache**
   - Railway caches build layers between deployments
   - Structure your Dockerfile to take advantage of layer caching

2. **Railway CLI**
   - For quick fixes, consider using the Railway CLI for direct deployments
   ```bash
   railway up
   ```

3. **GitHub Actions**
   - Set up GitHub Actions to control when Railway deployments are triggered
   - Example workflow in `.github/workflows/railway-deploy.yml`

   The provided GitHub Actions workflow will:
   - Deploy to Railway only when changes are pushed to the main branch
   - Skip deployments for documentation changes (saves build resources)
   - Allow manual triggering with the workflow_dispatch event
   - Require a Railway API token stored in GitHub Secrets

   To set up the Railway token:
   1. Generate a Railway token with the Railway CLI: `railway login`
   2. Add the token as a secret named `RAILWAY_TOKEN` in your GitHub repository settings

## Best Practices

### Docker Optimization

1. **Layer Caching**
   - Order Dockerfile commands from least to most frequently changing
   - Install dependencies before copying application code
   - Use .dockerignore to exclude unnecessary files

2. **Image Size**
   - Use slim base images when possible
   - Remove unnecessary packages and files
   - Consider multi-stage builds for production

3. **Development vs Production**
   - Development: Mount volumes for real-time code updates
   - Production: Copy code into container for security and isolation

### Environment Variables

- Never commit sensitive information to version control
- Use environment-specific variables:
  - `ENVIRONMENT=development` for local development
  - `ENVIRONMENT=production` for deployment

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Ensure the database service is running (`docker-compose ps`)
   - Check that the DATABASE_URL uses the correct hostname (`db` in docker-compose)

2. **Port Conflicts**
   - If port 8000 or 5432 is already in use, change the port mapping in docker-compose.yml

3. **Container Won't Start**
   - Check logs with `.\dev.ps1 logs`
   - Ensure all required environment variables are set

### Viewing Logs

```bash
# View logs for all services
.\dev.ps1 logs

# View logs for a specific service
docker-compose logs -f supportbot
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Railway Documentation](https://docs.railway.app/)
- [FastAPI with Docker](https://fastapi.tiangolo.com/deployment/docker/) 
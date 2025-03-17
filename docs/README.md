# Support Bot

A Telegram bot for managing support requests with a modern web interface and PostgreSQL backend.

## Latest Updates (2025-03-17)

- Fixed critical Application initialization error: "This Application was not initialized via `Application.initialize`!"
- Added proper initialization sequence for both Bot and Application objects (python-telegram-bot v20+ requirement)
- Improved error handling for bot initialization and webhook setup
- Added container-to-container network communication for local development
- Enhanced WebApp URL configuration with improved fallback mechanisms
- Created a comprehensive [Troubleshooting Guide](./TROUBLESHOOTING.md) for common issues
- Fixed critical bot initialization order error: "The parameter `bot` may only be set, if no connection_pool_size was set"
- Updated Application builder chain order to set bot instance first
- Enhanced documentation for proper initialization sequence
- Added comprehensive session logs for debugging
- Optimized bot initialization sequence
- Enhanced error handling and recovery mechanisms
- Improved deployment configuration for Railway

## Technical Details

### Bot Initialization
The bot uses a specific initialization sequence that MUST follow this order:

```python
bot_app = (
    Application.builder()
    .bot(bot)                        # Must be set first
    .concurrent_updates(True)
    .pool_timeout(POOL_TIMEOUT)      # Pool settings after bot
    .connection_pool_size(MAX_CONNECTIONS)
    .build()
)
```

> **Important**: The bot instance MUST be set before any connection pool configuration.

### Connection Pool Configuration
```python
# Environment variables
POOL_TIMEOUT = 30  # seconds
MAX_CONNECTIONS = 100
```

### Health Checks
The application includes comprehensive health checks:
```python
async def check_database():
    try:
        async with Session() as session:
            await session.execute(text("SELECT 1"))
            await session.commit()
            return True
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")
        return False
```

## Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Telegram Bot Token
- Railway account (for deployment)

### Installation
```bash
git clone https://github.com/yourusername/support-bot.git
cd support-bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Configuration
Create `.env` file:
```env
SUPPORT_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:port/dbname
POOL_TIMEOUT=30
MAX_CONNECTIONS=100
```

### Run Locally
```bash
python run.py
```

## Documentation

### Core Documentation
- [Installation Guide](INSTALLATION.md) - Detailed setup instructions
- [Deployment Guide](DEPLOYMENT.md) - Railway deployment walkthrough
- [Technical Documentation](TECHNICAL.md) - Architecture and components
- [API Documentation](API.md) - API reference
- [Changelog](CHANGELOG.md) - Version history

### Additional Resources
- [Database Guide](DATABASE.md) - Database management
- [Monitoring Guide](MONITORING.md) - System monitoring

## Project Structure
```
support-bot/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration
│   ├── api/
│   │   └── routes/       # API endpoints
│   ├── bot/
│   │   ├── bot.py       # Bot initialization
│   │   └── handlers/    # Command handlers
│   ├── database/
│   │   ├── models.py    # Database models
│   │   └── session.py   # Database connection
│   └── logging/
│       └── setup.py     # Logging configuration
├── docs/                # Documentation
├── alembic/             # Database migrations
└── run.py              # Entry point
```

## Key Features

### Bot Initialization
- Optimized connection pool management
- Proper initialization sequence
- Comprehensive error handling
- Automatic recovery mechanisms

### Database Integration
- PostgreSQL with SQLAlchemy ORM
- Connection pooling
- Alembic migrations
- Optimized queries

### API Endpoints
- Support request management
- Chat functionality
- Logging and monitoring
- Health checks

### Error Handling
- Comprehensive error catching
- Automatic recovery mechanisms
- Enhanced logging for debugging
- Connection pool monitoring

### Monitoring
- Real-time metrics collection
- Health check system
- Performance tracking
- Error monitoring

## Best Practices

### Connection Pool Management
1. Configure pool settings before bot instance
2. Monitor connection usage
3. Implement proper timeout handling
4. Regular health checks

### Error Handling
1. Use comprehensive error catching
2. Implement recovery mechanisms
3. Maintain detailed logging
4. Monitor system health

### Testing
1. Regular health checks
2. Connection pool monitoring
3. Performance verification
4. Error recovery testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Project Structure

```
support-bot/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/       # API endpoints
│   │       ├── chat.py
│   │       ├── support.py
│   │       └── logs.py
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── bot.py       # Bot initialization
│   │   └── handlers/    # Command handlers
│   │       ├── start.py
│   │       ├── support.py
│   │       └── admin.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py    # SQLAlchemy models
│   │   └── session.py   # Database connection
│   └── logging/
│       ├── __init__.py
│       ├── handlers.py  # Custom log handlers
│       └── setup.py     # Logging configuration
├── docs/               # Documentation
├── alembic/            # Database migrations
├── run.py             # Application entry point
├── requirements.txt    # Dependencies
├── Procfile           # Railway deployment
└── railway.toml       # Railway configuration
```

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (provided by Railway)
- Telegram Bot Token
- Railway account for deployment

## Environment Variables

Create a `.env` file with the following variables:

```env
SUPPORT_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:port/dbname
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/support-bot.git
cd support-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
alembic upgrade head
```

## Running Locally

Start the application:
```bash
python run.py
```

The bot will be available at `http://localhost:8080`.

## API Endpoints

### Chat Routes
- `GET /api/chat/{request_id}` - Get chat history
- `GET /api/chats` - List all chats

### Support Routes
- `POST /api/requests` - Create support request
- `PUT /api/requests/{request_id}` - Update request
- `POST /api/requests/{request_id}/messages` - Add message

### Log Routes
- `GET /api/logs` - Get application logs
- `GET /api/logs/recent` - Get recent logs
- `GET /api/logs/levels` - Get log level statistics

## Database Schema

### Request Model
```python
class Request:
    id: int
    user_id: int
    issue: str
    assigned_admin: Optional[int]
    status: str
    solution: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### Message Model
```python
class Message:
    id: int
    request_id: int
    sender_id: int
    sender_type: str  # 'user' or 'admin'
    message: str
    timestamp: datetime
```

### Log Model
```python
class Log:
    id: int
    timestamp: datetime
    level: str
    message: str
    context: str
```

## Deployment

### Railway Deployment

1. Push your changes to GitHub
2. Create a new project in Railway
3. Connect your GitHub repository
4. Add the following environment variables in Railway dashboard:
   - `SUPPORT_BOT_TOKEN`: Your Telegram bot token
   - `DATABASE_URL`: Will be auto-configured by Railway

The deployment is configured through `railway.toml`:
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python run.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

The `Procfile` handles web server startup and database migrations:
```
web: python run.py
release: alembic upgrade head
```

## Documentation

- [Changelog](CHANGELOG.md) - Version history and changes
- [Conversation History](CONVERSATION_HISTORY.md) - Development process
- [API Documentation](https://github.com/yourusername/support-bot/wiki) - Detailed API docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

### Deployment Configuration Details

The application uses the following deployment configuration in `railway.toml`:
```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python run.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

This configuration ensures:
- Proper dependency installation
- Correct entry point usage
- Health monitoring
- Automatic recovery on failures 

# Documentation Index

## Core Documentation Files

### 1. Project Documentation
- `README.md` (root) - Project overview and quick start
- `CHANGELOG.md` - Version history and changes
- `CONTRIBUTING.md` - Contribution guidelines

### 2. Technical Documentation
- `API.md` - Complete API reference and integration guide
  - API endpoints
  - Authentication
  - Request/response formats
  - Error handling
  - Rate limiting
  - CORS and security
  - Performance optimizations
  - Integration examples

- `DATABASE.md` - Database implementation and optimization
  - Connection pooling
  - Query optimization
  - Schema management
  - Maintenance procedures
  - Performance tuning
  - Backup and recovery

- `MONITORING.md` - System monitoring and metrics
  - Dashboard setup and usage
  - Metrics collection
  - System resource monitoring
  - Custom metrics
  - Alert configuration
  - Performance tracking

### 3. Development History
- `CONVERSATION_HISTORY.md` - Development sessions and decisions
  - Session logs
  - Key decisions
  - Implementation details
  - Technical discussions
  - Problem-solving approaches

## Documentation Standards

### File Organization
- Each documentation file focuses on a specific aspect
- Cross-references between files when needed
- Consistent formatting using Markdown
- Code examples where relevant

### Maintenance Guidelines
1. Update relevant docs with each feature change
2. Keep cross-references up to date
3. Add new sessions to conversation history
4. Update changelog with version changes
5. Review and sync documentation regularly

### Version Control
- Documentation versions match code releases
- Each major version has complete documentation
- Changes are tracked in CHANGELOG.md
- Documentation updates are part of pull requests

## Quick Links

| File | Purpose | Last Updated |
|------|----------|--------------|
| [README.md](../README.md) | Project overview | 2025-03-17 |
| [API.md](API.md) | API reference | 2025-03-17 |
| [DATABASE.md](DATABASE.md) | Database guide | 2025-03-17 |
| [MONITORING.md](MONITORING.md) | Monitoring guide | 2025-03-17 |
| [CHANGELOG.md](../CHANGELOG.md) | Version history | 2025-03-17 |
| [CONVERSATION_HISTORY.md](CONVERSATION_HISTORY.md) | Development logs | 2025-03-17 |

## Documentation TODOs

1. [ ] Add user documentation
2. [ ] Create deployment guide
3. [ ] Add performance benchmarking guide
4. [ ] Create troubleshooting guide
5. [ ] Add security best practices 

## Testing

For comprehensive information on testing the Support Bot, please refer to:

- [TESTING.md](TESTING.md) - Full documentation on testing procedures and utilities
- [LOCAL-TESTING.md](../tests/LOCAL-TESTING.md) - Detailed instructions for local testing setups

The project includes a dedicated test suite in the `tests/` directory with utilities for:
- Bot connection testing 
- Webhook management
- WebApp URL testing
- Local browser-based WebApp testing 
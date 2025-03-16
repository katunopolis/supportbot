# Support Bot

A Telegram bot for managing support requests with a modern web interface and PostgreSQL backend.

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
| [README.md](../README.md) | Project overview | 2024-03-22 |
| [API.md](API.md) | API reference | 2024-03-22 |
| [DATABASE.md](DATABASE.md) | Database guide | 2024-03-22 |
| [MONITORING.md](MONITORING.md) | Monitoring guide | 2024-03-22 |
| [CHANGELOG.md](../CHANGELOG.md) | Version history | 2024-03-22 |
| [CONVERSATION_HISTORY.md](CONVERSATION_HISTORY.md) | Development logs | 2024-03-22 |

## Documentation TODOs

1. [ ] Add user documentation
2. [ ] Create deployment guide
3. [ ] Add performance benchmarking guide
4. [ ] Create troubleshooting guide
5. [ ] Add security best practices 
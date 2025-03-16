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
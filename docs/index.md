# Support Bot Documentation

Welcome to the Support Bot documentation. This documentation provides comprehensive information about the Support Bot project, its features, setup instructions, and development history.

## Documentation Structure

- [README.md](README.md) - Project overview, setup instructions, and usage guide
- [CHANGELOG.md](CHANGELOG.md) - Version history and detailed changes for each release
- [CONVERSATION_HISTORY.md](CONVERSATION_HISTORY.md) - Development process and major decisions

## Project Overview

Support Bot is a Telegram bot designed to manage support requests efficiently. It features:

- PostgreSQL database for persistent storage
- FastAPI backend with modular architecture
- Web interface for support request management
- Comprehensive logging system
- Railway deployment support

## Directory Structure

```
support-bot/
├── app/
│   ├── api/
│   │   └── routes/      # API endpoints
│   ├── bot/
│   │   └── handlers/    # Telegram bot handlers
│   ├── database/        # Database models and session management
│   └── logging/         # Logging configuration
├── docs/               # Documentation
└── alembic/            # Database migrations
```

## Quick Links

- [Installation Guide](README.md#installation)
- [Environment Setup](README.md#environment-variables)
- [API Documentation](README.md#api-endpoints)
- [Latest Changes](CHANGELOG.md#version-120)
- [Development History](CONVERSATION_HISTORY.md) 
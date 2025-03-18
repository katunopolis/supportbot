# Support Bot Documentation

This folder contains comprehensive documentation for the Support Bot project.

## Code Structure

- [CODE-MAP.md](CODE-MAP.md) - Comprehensive overview of codebase structure and interactions
- [WEBAPP-CODE-MAP.md](WEBAPP-CODE-MAP.md) - Detailed documentation of the WebApp frontend components
- [CIRCULAR-DEPENDENCY-FIX.md](CIRCULAR-DEPENDENCY-FIX.md) - How circular dependencies were resolved

## Setup and Configuration

- [SETUP.md](SETUP.md) - Setup and installation instructions
- [CONFIG-SETTINGS.md](CONFIG-SETTINGS.md) - Configuration options and environment variables
- [LOCAL-DEVELOPMENT.md](LOCAL-DEVELOPMENT.md) - Local development environment setup
- [DOCKER.md](DOCKER.md) - Docker configuration and usage

## API and Data Models

- [API.md](API.md) - API documentation
- [CHAT-API.md](CHAT-API.md) - Chat API specific documentation
- [DATABASE.md](DATABASE.md) - Database schema and migrations

## User Interfaces

- [WEBAPP-CHAT-INTERFACE.md](WEBAPP-CHAT-INTERFACE.md) - WebApp chat interface documentation
- [ADMIN-CHAT-INTERFACE.md](ADMIN-CHAT-INTERFACE.md) - Admin chat interface documentation

## Testing and Monitoring

- [TESTING.md](TESTING.md) - Testing instructions and test cases
- [LOCAL-TESTING.md](LOCAL-TESTING.md) - Local testing procedures
- [MONITORING.md](MONITORING.md) - Monitoring and observability

## Troubleshooting and History

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [CHANGELOG.md](CHANGELOG.md) - History of changes
- [CONVERSATION_HISTORY.md](CONVERSATION_HISTORY.md) - Development conversation history

## Documentation Index

### Setup & Installation

- [SETUP.md](SETUP.md) - Complete guide for setting up the project on a new machine
- [CONFIG-SETTINGS.md](CONFIG-SETTINGS.md) - Configuration settings and environment variables

### Testing & Development

- [TESTING.md](TESTING.md) - Guide for testing the bot locally and in production
- [LOCAL-DEVELOPMENT.md](LOCAL-DEVELOPMENT.md) - Guide for local development
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and their solutions

### Architecture & API

- [API.md](API.md) - API documentation
- [DATABASE.md](DATABASE.md) - Database schema and models
- [CODE-MAP.md](CODE-MAP.md) - Overall codebase structure and interactions
- [WEBAPP-CODE-MAP.md](WEBAPP-CODE-MAP.md) - WebApp frontend architecture and components

### Project Information

- [CHANGELOG.md](CHANGELOG.md) - Project version history and changes

## Getting Started

If you're new to the project, here's how to get started:

1. Clone the repository
2. Run `python setup.py` and select "Full Setup"
3. Start ngrok with `ngrok http 8000`
4. Update the ngrok URL with `python fresh-setup/ngrok_update.py`
5. Test your bot by sending `/test` command

For detailed instructions, see the documentation below.

## Contributing to Documentation

When updating or adding documentation:

1. Use Markdown format
2. Follow the existing style and structure
3. Keep language clear and concise
4. Add links to other relevant documents
5. Update this index when adding new files 

## Recent Updates

### New Setup Tools
- **setup.py**: A comprehensive setup script that automates the process of setting up the bot on a new machine. It checks for dependencies, sets up environment variables, configures the database, and builds Docker containers.

- **ngrok_installer.py**: A dedicated installer for ngrok that addresses common installation issues. It downloads the correct version, installs it to the proper location, and adds it to your PATH.

- **ngrok-update utility**: A tool for updating the ngrok URL when it changes. Run `python fresh-setup/ngrok_update.py` to update all configuration files and restart services.

### Command Handling Fix
The bot now properly responds to all commands (/start, /help, /request, etc.). This was fixed by ensuring the Application is properly initialized with `await bot_app.initialize()` call.

### Troubleshooting Utilities
New troubleshooting tools have been added to help diagnose and fix common issues:
- `fix_ngrok.py`: Helps diagnose and fix ngrok-related issues
- `ngrok_installer.py`: Provides a reliable way to install ngrok on any platform

### New Setup Script and Cross-Machine Migration

We've added a new setup script (`setup.py`) in the project root that automates the process of setting up the Support Bot on a new machine. The script:

- Checks for required dependencies (Docker, ngrok, Python)
- Sets up environment variables
- Configures database settings
- Builds Docker containers

For detailed instructions on using this script or manually setting up on a new machine, see [SETUP.md](SETUP.md).

### ngrok URL Update Utility

We've also added a new utility for updating ngrok URLs when they change:

```bash
python run_test.py ngrok-update
```

This utility automatically updates all relevant configuration files with the new ngrok URL, restarts services, and sets up the webhook. 
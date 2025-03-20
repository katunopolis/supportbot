# Support Bot Documentation

Welcome to the Support Bot documentation! This section provides comprehensive information about the support bot's functionality, configuration, and development guidelines.

## Overview

The Support Bot is a Telegram-based customer support system that:

1. Allows users to submit support requests via a WebApp interface
2. Notifies admins in a group chat about new requests 
3. Provides a real-time chat interface for communication between users and admins
4. Supports admin actions like assigning and resolving requests
5. Enables admins to provide detailed solutions when resolving requests
6. Notifies users about request status changes and resolutions

## Key Features

- **User-friendly WebApp interface** for submitting support requests
- **Real-time chat** between users and support admins
- **Admin notification system** for new support requests
- **Admin action buttons** for quick handling of requests
- **Solution entry flow** when resolving requests
- **Automatic notifications** to users when their requests are solved
- **Persistent storage** of all support conversations
- **Secure authentication** via Telegram

## Getting Started

- [Setup Guide](SETUP.md) - Instructions for setting up the Support Bot
- [Local Development](LOCAL-DEVELOPMENT.md) - Guide for local development
- [Testing](TESTING.md) - How to test the bot components
- [Configuration](CONFIG-SETTINGS.md) - Available configuration options

## Architecture and Components

- [Code Map](CODE-MAP.md) - Overview of the codebase structure
- [WebApp Code Map](WEBAPP-CODE-MAP.md) - WebApp architecture details
- [Database Schema](DATABASE.md) - Database models and relationships
- [API Documentation](API.md) - API endpoints and usage
- [Chat Interface](WEBAPP-CHAT-INTERFACE.md) - How the chat interface works
- [Docker Setup](DOCKER.md) - Docker configuration and usage

## Admin Documentation

- [Admin Chat Interface](ADMIN-CHAT-INTERFACE.md) - How admins interact with the chat
- [Admin Workflows](ADMIN-WORKFLOW.md) - Common admin workflows
- [Monitoring](MONITORING.md) - Monitoring and logging features

## Technical Documentation

- [Circular Dependency Fix](CIRCULAR-DEPENDENCY-FIX.md) - Resolving circular import issues
- [Local Testing](LOCAL-TESTING.md) - Testing procedures for development
- [Troubleshooting](TROUBLESHOOTING.md) - Solutions for common problems
- [Changelog](CHANGELOG.md) - History of changes and releases

## Recent Updates

### Enhanced Admin Solution Flow

We've added an improved workflow for request resolution:

1. When an admin clicks the "Solve" button on a request:
   - The bot prompts the admin to provide solution details
   - The admin can enter a detailed solution text in a private chat with the bot
   
2. After the admin provides the solution:
   - The request is marked as solved in the database
   - The solution text is stored with the request
   - The user receives a notification with the solution details
   - The admin group is notified that the request was resolved
   
3. Key benefits:
   - Better documentation of request resolutions
   - More helpful notifications for users
   - Improved tracking of admin actions

### Fixed Issues

Recent fixes include:

1. **Circular Import Resolution** - Improved the code architecture to handle circular dependencies
2. **Database Field Consistency** - Ensured consistency between code models and database schema
3. **Callback Pattern Matching** - Fixed button handling to ensure consistent pattern matching
4. **Bot Reference Handling** - Added proper error handling for bot references

## Contribution

Please refer to our [contribution guidelines](CONTRIBUTING.md) if you want to contribute to the Support Bot project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
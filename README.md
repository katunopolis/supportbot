# Telegram Support Bot

A comprehensive support bot for Telegram that enables users to submit support requests and chat with admins through a WebApp interface.

## Features

- Support request submission through WebApp
- Real-time chat between users and admins
- PostgreSQL database for persistent storage
- Automatic database migrations with Alembic
- Enhanced logging system with both file and database handlers
- Responsive WebApp design with Telegram theme support
- Admin assignment and request management
- Webhook-based updates handling

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (provided by Railway)
- Telegram Bot Token
- Railway account for deployment

## Environment Variables

```env
SUPPORT_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_postgresql_connection_url
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/support-bot.git
cd support-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
- Create a new PostgreSQL service in Railway
- Copy the connection URL to your environment variables

4. Initialize the database:
```bash
alembic upgrade head
```

## Deployment on Railway

1. Create a new project in Railway
2. Add your repository
3. Add PostgreSQL service
4. Set environment variables:
   - `SUPPORT_BOT_TOKEN`
   - `DATABASE_URL` (automatically provided by Railway)
5. Deploy the application

## Project Structure

```
support-bot/
├── supportbot.py        # Main bot application
├── database.py          # Database models and configuration
├── alembic/            # Database migrations
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment configuration
└── webapp-support-bot/
    ├── index.html     # Support request form
    └── chat.html      # Support chat interface
```

## Database Schema

### Requests
- id (Primary Key)
- user_id (Integer)
- issue (Text)
- assigned_admin (Integer, nullable)
- status (Text)
- solution (Text, nullable)

### Messages
- id (Primary Key)
- request_id (Foreign Key)
- sender_id (Integer)
- sender_type (Text)
- message (Text)
- timestamp (DateTime)

### Logs
- id (Primary Key)
- timestamp (DateTime)
- level (Text)
- message (Text)
- context (Text)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Key Features
- Telegram WebApp integration
- Real-time support chat
- Admin assignment system
- Extensive logging system
- Platform-specific UI adjustments
- Comprehensive error handling
- Theme-aware interface
- Session continuity management

## Development Guidelines

### Session Management
- Update CHANGELOG.md before closing each session
- Document all changes made during the session
- Include technical details and context
- Note platform-specific changes
- Document error scenarios and solutions
- Keep track of pending tasks

### Code Documentation
- All major functions must have JSDoc-style comments
- CSS sections should be documented with purpose
- HTML elements should have descriptive comments
- Platform-specific code should be clearly marked
- Logging calls should include context
- Document all state changes and transitions
- Include error handling documentation

### WebApp Integration
- Always use `tg.MainButton` for primary actions
- Handle both WebApp and browser environments
- Implement proper error recovery
- Log all button state changes
- Use centralized logging functions
- Handle platform-specific events
- Document WebApp lifecycle events

### Logging System
- All logs are stored in SQLite database
- Endpoint: `https://supportbot-production-b784.up.railway.app/logs`
- Log format includes:
  - Timestamp
  - Level (info/error)
  - Message
  - Context (platform, user, state)
- Use `logButtonState()` for button events
- Use `logWebAppEvent()` for general events
- Include relevant context in all logs

### Error Handling
1. Always implement fallbacks
2. Log all errors with context
3. Provide user feedback
4. Recover gracefully
5. Use try-catch blocks
6. Document error scenarios
7. Include error recovery steps
8. Log error resolution

### Theme Handling
- Use Telegram theme variables
- Update on theme changes
- Support both light/dark modes
- Use CSS variables for colors
- Handle theme changes gracefully
- Document theme-related issues
- Test theme transitions

### Platform Support
- iOS/Android specific adjustments
- Desktop optimizations
- Safe area insets
- Viewport changes
- Back button handling
- Platform-specific logging
- Cross-platform testing

## Common Issues & Solutions
1. **Invalid Button Error**
   - Ensure proper button initialization
   - Use try-catch blocks
   - Implement fallback buttons
   - Log button state changes
   - Document initialization sequence

2. **WebApp Integration**
   - Check platform compatibility
   - Handle viewport changes
   - Manage button states properly
   - Use centralized logging
   - Document platform differences

3. **Theme Issues**
   - Use CSS variables
   - Handle theme changes
   - Provide fallback colors
   - Test in both modes
   - Document theme variables

4. **Session Continuity**
   - Update documentation before closing
   - Document pending tasks
   - Note known issues
   - Track feature status
   - Maintain change history

## Testing
- Test on multiple platforms (iOS, Android, Desktop)
- Verify logging system
- Check error recovery
- Test theme changes
- Validate button states
- Test viewport changes
- Verify safe areas
- Test session continuity
- Validate documentation

## Deployment
Current endpoints:
- Bot: `https://supportbot-production-b784.up.railway.app`
- WebApp: `https://webapp-support-bot-production.up.railway.app`

## Documentation
- Keep CHANGELOG.md updated
- Document all major changes
- Include technical details
- Note platform-specific changes
- Document error scenarios
- Track session changes
- Maintain development history
- Document pending tasks

## Railway Deployment Guide

### Prerequisites
1. Python 3.11 environment
2. Railway account
3. GitHub repository
4. Bot token from @BotFather

### Deployment Steps
1. **Environment Setup**
   ```bash
   # Create virtual environment
   py -3.11 -m venv venv
   
   # Activate virtual environment
   # Windows
   .\venv\Scripts\activate
   # Linux/MacOS
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Railway Configuration**
   - Connect GitHub repository to Railway
   - Set environment variables:
     - `SUPPORT_BOT_TOKEN`
     - `DATABASE_URL` (automatically provided by Railway)
   - Deploy application
   - Verify webhook setup

3. **Verification**
   - Check health endpoint: `/health`
   - Verify webhook status
   - Test bot commands
   - Monitor logs

### Environment Variables
```env
SUPPORT_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=your_postgresql_connection_url
```

### Monitoring
- Health check endpoint: `/health`
- Logs endpoint: `/logs`
- WebApp logs: `/webapp-log`
- Database status: Check `support_requests.db`

### Troubleshooting
1. **Webhook Issues**
   - Verify SSL certificate
   - Check Railway URL
   - Confirm bot token
   - Monitor webhook logs

2. **Database Issues**
   - Check permissions
   - Verify initialization
   - Monitor disk space
   - Check connections

3. **Python Environment**
   - Verify Python 3.11
   - Check dependencies
   - Monitor virtual env
   - Update packages

## Production Setup

### Security
- SSL certificate verification
- Secure webhook endpoints
- Database access control
- Error logging protection

### Performance
- Database optimization
- Log rotation
- Cache management
- Request throttling

### Monitoring
- Health checks
- Error tracking
- User activity
- System resources

### Backup
- Database backups
- Log archives
- Configuration backup
- Recovery procedures

## System Requirements

### Minimum Requirements
- Python 3.11+
- 512MB RAM
- 1GB storage
- SSL certificate

### Recommended
- Python 3.11.5+
- 1GB RAM
- 2GB storage
- Dedicated SSL
- Monitoring tools

## Support and Maintenance

### Regular Tasks
1. Monitor logs
2. Check health status
3. Verify webhooks
4. Update dependencies
5. Backup database

### Emergency Procedures
1. Check error logs
2. Verify connections
3. Restart services
4. Contact support
5. Restore backups

## Contact

For deployment issues or support:
1. Check logs at `/logs`
2. Monitor health at `/health`
3. Review webhook status
4. Contact maintainers
5. Submit issue ticket 
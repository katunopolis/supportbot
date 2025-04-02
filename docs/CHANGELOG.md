# Changelog

All notable changes to the Support Bot project will be documented in this file.

## [1.2.4] - 2025-04-04 BUGFIX

### Added
- **ISO 8601 Timestamp Handling**: Implemented robust ISO 8601 timestamp processing throughout the application
- **Client-Server Time Synchronization**: Added mechanism to detect and adjust for time differences between client and server
- **Timezone Awareness**: Enhanced chat interface to properly handle messages across different timezones
- **Time Difference Indicators**: Added visual indicators when significant time differences exist between client and server
- **Context-Aware Time Display**: Messages now show date context for older messages while keeping today's messages clean
- **Multiple Time Formats**: Added support for various ISO 8601 timestamp formats (Z suffix, timezone offset, etc.)
- **Server Time Headers**: Added X-Server-Time response headers for precise synchronization
- **Real-time Clock Display**: Added client and server time display in chat header

### Fixed
- **2-Hour Timezone Shift**: Fixed critical issue where messages appeared with incorrect timestamps (2 hours off)
- **Message Ordering**: Resolved issues where messages could appear out of order due to timezone differences
- **Timestamp Parsing**: Enhanced timestamp parsing with multiple fallback mechanisms for various formats
- **Time Display Consistency**: Fixed inconsistent time display between new and existing messages
- **Polling Reliability**: Improved polling timestamp handling to prevent missed messages
- **UTC vs Local Time**: Fixed confusion between UTC and local time in message displays

### Changed
- **Timestamp Storage**: All timestamps now standardized as ISO 8601 with UTC timezone (Z suffix)
- **Message Time Display**: Enhanced to show both local time and UTC when they differ significantly
- **API Time Headers**: Enhanced request/response headers to include timezone information
- **Documentation**: Updated all API and interface documentation to reflect new timestamp handling

## [1.2.3] - 2025-04-03 ENHANCEMENT

### Changed
- **WebApp Theming System**: Standardized WebApp theme handling across all HTML interfaces
- **Theme Integration**: Implemented proper use of Telegram's WebApp theming variables
- **Dynamic Theme Updates**: Added support for real-time theme changes via 'themeChanged' event
- **Theme Parameters**: Updated all interfaces to use tg.themeParams directly instead of deprecated properties
- **UI Consistency**: Ensured consistent color usage across all WebApp interfaces

### Removed
- **Hardcoded Colors**: Eliminated all hardcoded color values from the CSS
- **Theme Meta Tags**: Removed unnecessary theme-color meta tags
- **External Stylesheets**: Removed external CSS that might override Telegram theme colors
- **Fallback Colors**: Removed hardcoded fallback colors to ensure proper Telegram theming

## [1.2.2] - 2025-04-02 BUGFIX

### Fixed
- **Support Request Endpoint**: Fixed the `/support-request` endpoint in web application to properly route requests to the working API endpoint (`/api/support/request`) in the supportbot service
- **API Integration**: Improved error handling in the webapp's server.js to better capture and report API errors
- **Logging Enhancement**: Updated log messages to clearly show request routing paths

## [1.2.1] - 2025-03-20 STABLE

### Fixed
- **Message Visibility**: Fixed critical issue where admins and users could only see their own messages in chat
- **Timestamp Handling**: Resolved timezone-related issues causing messages to be missed or displayed out of order
- **API Routing**: Fixed routing in main.py to properly direct chat/message API requests to appropriate handlers
- **Cross-Timezone Compatibility**: Ensured consistent handling of timestamps across different client time zones
- **Message Deduplication**: Added message ID tracking to prevent duplicate messages when reconnecting
- **UI Enhancement**: Added clear sender labels to improve chat readability

### Added
- **Improved Error Handling**: Added robust fallback mechanisms for timestamp parsing failures
- **Enhanced Logging**: Added detailed logging for timestamp-related operations
- **Verification Tests**: Created test scripts to verify timestamp handling across formats
- **UI Indicator**: Added version indicator in chat interface (v1.2.1) to track deployed version

### Changed
- **Standardized Timestamps**: All timestamps now consistently use ISO 8601 format with UTC timezone ('Z' suffix)
- **Message Styling**: Updated message bubble styling to better differentiate between sender types

## [Unreleased]

### Added
- Enhanced solution message flow for admin resolution
- Support for admin to provide detailed solution when resolving a request
- Automatic notification to user with solution details after request is resolved
- User and admin group both receive the solution text in notifications
- Improved logging system with better formatting and filtering
- Database logging handler for persistent log storage
- Smart filtering for HTTP and Telegram bot messages
- Enhanced log readability in Docker container output

### Fixed
- Fixed circular import issues in bot.py and handlers files
- Resolved database field name mismatch between code and schema
- Fixed callback pattern matching to ensure proper handler selection
- Added proper error handling for missing bot reference
- Fixed circular import issues in logging setup
- Resolved message attribute error in log filtering
- Improved database connection handling in log storage
- Fixed timestamp handling in log messages

## [0.3.0] - 2025-03-18

### Added
- WebApp interface for users to submit support requests
- Real-time chat interface for communication between users and admins
- Admin group notifications for new support requests 
- Admin buttons for quick actions (Open Chat, Solve)
- Solution entry prompt when admin resolves a request
- Support for attaching solution details to closed requests

### Changed
- Improved error handling throughout the application
- Enhanced logging for better debugging
- Updated database schema to include solution field
- Streamlined admin workflow for request handling
- Updated log format to be more human-readable
- Reduced noise in logs by filtering routine messages
- Improved error handling in logging system
- Updated documentation with comprehensive logging guide

### Fixed
- Resolved issues with WebApp message polling
- Fixed callback query handling for admin actions
- Addressed circular dependencies between modules
- Corrected field name inconsistencies in database models

## [0.2.1] - 2025-03-15

### Added
- Global error handling in the Telegram bot
- Database connection pooling for improved performance
- Rate limiting for API endpoints to prevent abuse
- Throttling for Telegram bot requests

### Fixed
- Message delivery issues for long text
- Database connection leaks
- Improved error messages for failed operations

## [0.2.0] - 2025-03-10

### Added
- Admin dashboard for viewing and managing support requests
- WebApp interface for users
- Chat history view with real-time updates
- Support for file uploads in chat
- Webhooks for integration with other services

### Changed
- Upgraded Telegram Bot API usage to latest version
- Improved database schema for better querying
- Enhanced user experience in the WebApp

### Fixed
- Several bugs in the message routing system
- Issues with concurrent message handling
- Problems with webhook setup

## [0.1.0] - 2025-03-01

### Added
- Initial release of the basic support bot
- Simple command-based interface
- Support for creating and viewing support requests
- Basic admin commands for handling requests
- SQLAlchemy integration for database operations
- Docker containerization for easy deployment

### Changed
- Moved from single-file structure to modular architecture
- Implemented async handlers for better performance

### Fixed
- Initial bugs in the command parsing logic
- Issues with database connections
- Problems with deployment scripts

## [Latest] - 2025-03-18

### Critical Chat System Fixes
- Fixed issue with support request submission not sending notifications to admin group
- Fixed "Failed to fetch" error when loading the chat interface after submitting a request
- Added direct handling of `/api/chat/` endpoints with fallback responses
- Implemented reliable `/fixed-chat/{request_id}` endpoint that always returns valid data
- Enhanced message polling with empty array responses for graceful degradation
- Fixed proxy routing to properly handle API requests and special routes
- Improved error handling with detailed logging throughout the system
- Added multiple fallback endpoints for chat history loading in the frontend

### WebApp Integration Improvements
- Implemented multiple fallback mechanisms for chat data loading
- Enhanced frontend error handling with better user feedback
- Fixed proxy logic to handle special route cases correctly
- Added better detection of chat-related API requests
- Improved real-time message polling reliability
- Enhanced support request submission workflow

## [Latest] - 2025-03-17

### WebApp Chat Interface Improvements
- Implemented Single-Page Application (SPA) approach to avoid redirect issues in Telegram WebApp
- Fixed critical error: "Failed to load chat: 404" when accessing chat interface
- Added missing API endpoint for retrieving messages since a specific timestamp
- Fixed proxy route in main.py to properly handle API requests
- Enhanced error handling with fallback mechanism for API failures
- Improved chat interface styling and user experience

### Bot Initialization and WebApp Integration Fix
- Fixed critical error: "This Application was not initialized via `Application.initialize`!" in command handling
- Added proper initialization sequence for both Bot and Application objects (python-telegram-bot v20+ requirement)
- Improved error handling for bot initialization and webhook setup
- Added container-to-container network communication for local development
- Enhanced WebApp URL configuration with improved fallback mechanisms

### Bot Initialization Order Fix
- Fixed critical error: "The parameter `bot` may only be set, if no connection_pool_size was set"
- Updated Application builder chain order to set bot instance first
- Enhanced documentation for proper initialization sequence
- Added comprehensive session logs for debugging

### Added
- Virtual environment setup with Python 3.11
- Database initialization and setup
- Webhook configuration for Railway deployment
- Bot startup and initialization logging
- SSL context configuration for secure connections
- Health check endpoint implementation
- Comprehensive logging system integration

### Fixed
- Python version compatibility issues resolved
- Webhook setup and verification process
- Database connection handling
- SSL certificate verification
- Bot initialization sequence

### Changed
- Updated Python runtime to 3.11
- Enhanced logging format and structure
- Improved webhook handling system
- Optimized database operations
- Enhanced error handling and recovery

### Technical Details
- Location of changes:
  - Virtual environment setup in `venv/`
  - Database initialization in `support_requests.db`
  - Logging configuration in `bot.log`
  - Bot initialization in `supportbot.py`

- Key components modified:
  - Python environment configuration
  - Database schema and initialization
  - Logging system setup
  - Webhook configuration
  - SSL context handling
  - Error recovery system

## [1.3.0] - 2025-03-16

### Infrastructure Updates
- Fixed critical connection pool configuration issues
- Optimized bot initialization sequence
- Enhanced error handling and recovery mechanisms
- Improved deployment configuration for Railway

### Database Migration Updates
- Updated connection pool settings
- Added health check implementations
- Enhanced error recovery mechanisms

### Railway Deployment and Environment Setup
- Python 3.11 virtual environment setup and configuration
- Railway deployment configuration and documentation
- Health check endpoint for monitoring
- Enhanced logging system with rotation
- SSL context configuration for secure connections
- Comprehensive error handling and recovery
- Database initialization and management improvements
- Webhook configuration for Railway deployment

### WebApp Improvements
- Extensive button state logging in WebApp
- Theme handling and automatic updates
- Viewport change handling
- Back button support with logging
- Closing confirmation for WebApp
- Comprehensive code documentation and comments
- Centralized logging functions for better maintainability
- CSS variables for Telegram theme colors
- Platform-specific UI adjustments

### Fixed
- Button type invalid error handling
- WebApp initialization issues
- Theme color application
- Message sending state management
- Duplicate logging code
- Inconsistent button state management
- Documentation gaps in code
- Missing context in logging calls

### Changed
- Improved error handling and recovery
- Enhanced logging system with context
- Better user feedback during operations
- Platform-specific adjustments for mobile/desktop
- Refactored logging functions for better code organization
- Improved CSS structure with proper comments
- Enhanced button state management
- Streamlined WebApp initialization process
- Updated documentation structure

### Deployment Success (2025-03-16)
- Successful deployment to Railway platform
- Confirmed working Alembic migrations with PostgreSQL
- Verified Python 3.12 compatibility
- All dependencies installed and working correctly
- Health check endpoint operational

## [Latest] - 2024-03-19

### Added
- Extensive button state logging in WebApp
- Virtual environment setup with Python 3.11
- Database initialization and setup
- Webhook configuration for Railway deployment
- Bot startup and initialization logging
- SSL context configuration for secure connections
- Health check endpoint implementation
- Comprehensive logging system integration

### Fixed
- Python version compatibility issues resolved
- Webhook setup and verification process
- Database connection handling
- SSL certificate verification
- Bot initialization sequence

### Changed
- Updated Python runtime to 3.11
- Enhanced logging format and structure
- Improved webhook handling system
- Optimized database operations
- Enhanced error handling and recovery

### Technical Details
- Location of changes:
  - Virtual environment setup in `venv/`
  - Database initialization in `support_requests.db`
  - Logging configuration in `bot.log`
  - Bot initialization in `supportbot.py`

- Key components modified:
  - Python environment configuration
  - Database schema and initialization
  - Logging system setup
  - Webhook configuration
  - SSL context handling
  - Error recovery system

## [Latest] - 2024-03-19

### Added
- Extensive button state logging in WebApp
- Theme handling and automatic updates
- Viewport change handling
- Back button support with logging
- Closing confirmation for WebApp
- Comprehensive code documentation and comments
- Centralized logging functions for better maintainability
- CSS variables for Telegram theme colors
- Platform-specific UI adjustments
- Documentation update system for session continuity
- JSDoc-style function documentation
- HTML element descriptive comments
- CSS section documentation
- Platform-specific code markers

### Fixed
- Button type invalid error handling
- WebApp initialization issues
- Theme color application
- Message sending state management
- Duplicate logging code
- Inconsistent button state management
- Documentation gaps in code
- Missing context in logging calls

### Changed
- Improved error handling and recovery
- Enhanced logging system with context
- Better user feedback during operations
- Platform-specific adjustments for mobile/desktop
- Refactored logging functions for better code organization
- Improved CSS structure with proper comments
- Enhanced button state management
- Streamlined WebApp initialization process
- Updated documentation structure
- Improved code readability with comprehensive comments
- Enhanced session continuity documentation

### Technical Details
- Location of changes:
  - `webapp-support-bot/index.html`
  - `webapp-support-bot/chat.html`
  - `support-bot/supportbot.py`
  - `support-bot/CHANGELOG.md`
  - `support-bot/README.md`

- Key components modified:
  - WebApp initialization
  - Button state management
  - Theme handling
  - Error recovery
  - Logging system
  - Code documentation
  - CSS structure
  - Platform-specific handling
  - Documentation system
  - Session management

## [0.1.0] - 2024-03-20

### Added
- Initial setup of the support bot project
- Created main bot script `supportbot.py` with Telegram bot functionality
- Added WebApp integration with `index.html` and `chat.html`
- Implemented support request submission and chat functionality
- Added database integration for storing support requests and messages
- Added logging system with both file and database handlers
- Implemented webhook handling for Telegram updates
- Added theme support for Telegram WebApp
- Added error handling and logging for WebApp events

### Fixed
- Resolved Python version compatibility issues
- Fixed WebApp button creation and display issues
- Improved error handling in message sending
- Enhanced theme handling for different platforms

### Technical Details
- Using Python 3.11 for compatibility
- Integrated FastAPI for webhook handling
- Using SQLite for data storage
- Implemented proper logging system
- Added WebApp support with responsive design 

## [1.2.0] - 2024-03-16

### Added
- PostgreSQL database integration using SQLAlchemy ORM
- Alembic for database migrations
- Proper database models for Requests, Messages, and Logs
- New environment variable `DATABASE_URL` for PostgreSQL connection
- Procfile for proper deployment on Railway
- Database session management with dependency injection
- Enhanced logging system with both file and database handlers

### Changed
- Migrated from SQLite to PostgreSQL for better scalability and persistence
- Updated all database operations to use SQLAlchemy ORM
- Improved error handling and logging throughout the application
- Enhanced button visibility and interaction in admin notifications
- Refactored webhook handling and initialization process

### Removed
- SQLite database and related code
- Direct SQL queries replaced with ORM operations

### Fixed
- Button visibility issues in admin group notifications
- Message formatting consistency
- Database connection persistence across service restarts
- Webhook initialization and verification process

### Technical Details
- Location of changes:
  - Database schema and migration scripts
  - Environment variable configuration
  - Procfile for deployment
  - Database session management
  - Logging system integration

- Key components modified:
  - Database schema design
  - ORM integration
  - Environment variable management
  - Procfile configuration
  - Database session handling
  - Logging system

## [Latest] - 2024-03-19

### Added
- Extensive button state logging in WebApp
- Theme handling and automatic updates
- Viewport change handling
- Back button support with logging
- Closing confirmation for WebApp
- Comprehensive code documentation and comments
- Centralized logging functions for better maintainability
- CSS variables for Telegram theme colors
- Platform-specific UI adjustments
- Documentation update system for session continuity
- JSDoc-style function documentation
- HTML element descriptive comments
- CSS section documentation
- Platform-specific code markers

### Fixed
- Button type invalid error handling
- WebApp initialization issues
- Theme color application
- Message sending state management
- Duplicate logging code
- Inconsistent button state management
- Documentation gaps in code
- Missing context in logging calls

### Changed
- Improved error handling and recovery
- Enhanced logging system with context
- Better user feedback during operations
- Platform-specific adjustments for mobile/desktop
- Refactored logging functions for better code organization
- Improved CSS structure with proper comments
- Enhanced button state management
- Streamlined WebApp initialization process
- Updated documentation structure
- Improved code readability with comprehensive comments
- Enhanced session continuity documentation

### Technical Details
- Location of changes:
  - `webapp-support-bot/index.html`
  - `webapp-support-bot/chat.html`
  - `support-bot/supportbot.py`
  - `support-bot/CHANGELOG.md`
  - `support-bot/README.md`

- Key components modified:
  - WebApp initialization
  - Button state management
  - Theme handling
  - Error recovery
  - Logging system
  - Code documentation
  - CSS structure
  - Platform-specific handling
  - Documentation system
  - Session management

## [0.1.0] - 2024-03-20

### Added
- Initial setup of the support bot project
- Created main bot script `supportbot.py` with Telegram bot functionality
- Added WebApp integration with `index.html` and `chat.html`
- Implemented support request submission and chat functionality
- Added database integration for storing support requests and messages
- Added logging system with both file and database handlers
- Implemented webhook handling for Telegram updates
- Added theme support for Telegram WebApp
- Added error handling and logging for WebApp events

### Fixed
- Resolved Python version compatibility issues
- Fixed WebApp button creation and display issues
- Improved error handling in message sending
- Enhanced theme handling for different platforms

### Technical Details
- Using Python 3.11 for compatibility
- Integrated FastAPI for webhook handling
- Using SQLite for data storage
- Implemented proper logging system
- Added WebApp support with responsive design 

## [1.3.0] - 2025-03-16

### Infrastructure Updates
- Fixed critical connection pool configuration issues
- Optimized bot initialization sequence
- Enhanced error handling and recovery mechanisms
- Improved deployment configuration for Railway

### Database Migration Updates
- Updated connection pool settings
- Added health check implementations
- Enhanced error recovery mechanisms

## [2024-03-16] - Bot Initialization Order Fix

### Fixed
- Critical error: "The parameter `bot` may only be set, if no connection_pool_size was set"
- Bot initialization sequence order
- Application startup failures

### Changed
- Updated Application builder chain order:
  1. Bot instance (must be first)
  2. Concurrent updates
  3. Pool timeout
  4. Connection pool size

### Technical Details
```python
# Previous implementation (causing errors)
bot_app = (
    Application.builder()
    .pool_timeout(POOL_TIMEOUT)
    .connection_pool_size(MAX_CONNECTIONS)
    .concurrent_updates(True)
    .bot(bot)
    .build()
)

# New implementation (fixed)
bot_app = (
    Application.builder()
    .bot(bot)                        # Must be set first
    .concurrent_updates(True)
    .pool_timeout(POOL_TIMEOUT)      # Pool settings after bot
    .connection_pool_size(MAX_CONNECTIONS)
    .build()
)
```

### Documentation
- Updated technical documentation with initialization process
- Added deployment configuration details
- Enhanced API documentation
- Improved installation guide

## [1.4.0] - 2025-03-17

### Added
- Admin chat interface via Telegram WebApp
- WebApp-based real-time chat between admins and users
- Chat API endpoints for message history and sending messages
- Support for Telegram theme integration in WebApp
- Configuration settings for WebApp URLs
- Comprehensive documentation for the chat interface

### Fixed
- Resolved circular dependencies between modules
- Fixed issue with admin notification for new support requests
- Improved error handling in WebApp interface
- Enhanced logging for debugging WebApp issues

### Changed
- Refactored bot initialization to avoid circular imports
- Improved API response structure for chat endpoints
- Enhanced admin view with WebApp button for chat interface
- Updated documentation with WebApp configuration information

## [1.2.1] - 2025-03-20

### Fixed
- **API Routing Issue**: Fixed critical issue in `main.py` where the proxy middleware was intercepting API requests before they could reach the intended endpoints. This was preventing proper handling of chat list and message polling requests.
- **ISO 8601 Timestamp Handling**: Implemented comprehensive ISO 8601 timestamp handling throughout the application, ensuring consistent timezone information (UTC) and format (with 'Z' suffix).
- **Chat Polling Logic**: Enhanced message polling logic to prevent multiple polling instances, handle errors gracefully, and use exponential backoff for retries.
- **Timestamp Validation**: Added robust timestamp validation and normalization on both frontend and backend to prevent issues with invalid timestamps.

### Added
- **Timestamp Test Script**: Created `test_timestamp_handling.py` script to verify proper timestamp formatting, parsing, and API interactions.
- **Timestamp Documentation**: Added detailed documentation for ISO 8601 timestamp handling in `TIMESTAMP-HANDLING.md`.
- **Troubleshooting Guide**: Updated troubleshooting guide with sections on chat polling and timestamp handling issues.

### Changed
- **Message Polling Endpoint**: Modified the message polling endpoint to properly handle and validate timestamp parameters.
- **Frontend Timestamp Management**: Updated frontend code to ensure all timestamps are in ISO 8601 format with proper UTC timezone indication.
- **API Response Format**: Standardized API response format for timestamps across all endpoints to ensure consistency.

## [1.2.0] - 2025-03-15

### Added
- **Admin Panel**: Implemented admin panel for managing support requests and conversations.
- **Webapp Integration**: Added seamless integration with Telegram WebApp for enhanced user experience.
- **Real-time Chat**: Implemented real-time chat functionality between users and admins.
- **Support Request Management**: Added comprehensive support request creation, tracking, and resolution system.

### Changed
- **API Structure**: Reorganized API endpoints for better maintainability and performance.
- **Database Models**: Enhanced database models with improved relationship handling.
- **Logging System**: Upgraded logging system with better error tracking and performance monitoring.

### Fixed
- **Bot Command Handling**: Fixed issues with bot command processing and rate limiting.
- **Webhook Setup**: Improved reliability of webhook setup and management.
- **Database Connections**: Enhanced database connection pooling and error handling.

## Version 1.2.1 (2025-03-20)

### Fixed
- **Critical:** Fixed chat message visibility issue where admin and user could only see their own messages
- **UI:** Added sender identification labels to messages for clarity
- **Technical:** Fixed user ID comparison to handle string and number type mismatches
- **Tech Debt:** Added message deduplication to prevent duplicate messages when reconnecting
- **UI:** Enhanced message styling to better differentiate between sender types
- **Developer:** Added extensive debug logging to aid future troubleshooting

### Added
- Added version indicator to chat interface (v1.2.1-fix)
- Added proper message sender labels ("You", "Admin", "User")
- Added data attributes to track message IDs for deduplication

### Changed
- Modified message bubble styling to improve visual clarity
- Updated ID comparison logic to use string conversion for consistent matching
- Improved error handling for message processing

## Version 1.2.0 (2025-03-15)

### Added
- Implemented admin panel for managing support requests
- Integrated with Telegram WebApp for enhanced user experience
- Added real-time chat functionality
- Created support request management system
- Implemented comprehensive timestamp handling with ISO 8601 format
- Added version tracking for easier debugging

### Changed
- Reorganized API endpoints for better maintainability
- Enhanced database models
- Upgraded logging system
- Standardized timestamp handling across frontend and backend

### Fixed
- Resolved issues with bot command handling
- Fixed webhook setup
- Fixed database connection issues
- Addressed timestamp formatting inconsistencies

## Version 1.1.0 (2025-03-01)

### Added
- Basic support request submission
- Admin notification system
- Simple chat capability
- User authentication via Telegram

### Changed
- Updated database schema
- Improved error handling
- Enhanced user interface

## Version 1.0.0 (2025-02-15)

### Added
- Initial bot structure
- Basic command handling
- Database integration
- Deployment setup
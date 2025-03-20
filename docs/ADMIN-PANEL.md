# Admin Panel Module

## Overview

The Admin Panel Module provides a Telegram WebApp interface for administrators to manage support requests. This module is designed to be modular and can be enabled or disabled without affecting the core functionality of the Support Bot.

![Admin Panel Interface](../assets/admin-panel-screenshot.png)

## Features

- **Request Dashboard**: View all open support requests in a single interface
- **Real-time Updates**: Dashboard refreshes automatically every 30 seconds
- **Quick Actions**: Open chat with users or solve requests directly from the panel
- **Theme Integration**: Automatically adapts to Telegram's theme settings
- **Responsive Design**: Works across different screen sizes and device types

## Configuration

The Admin Panel can be enabled or disabled using a simple environment variable:

```
# In your .env file
ADMIN_PANEL_ENABLED=true  # Set to "false" to disable
```

When disabled, the `/panel` command and related API endpoints will return appropriate messages indicating that the feature is currently unavailable.

## Usage

### Accessing the Admin Panel

The Admin Panel is accessible to administrators through the `/panel` command in the admin group chat. This command displays a button that opens the Admin Panel WebApp interface.

```
/panel
```

### Admin Panel Interface

The Admin Panel interface displays:

1. **Request List**: All currently open support requests
2. **Request Details**: 
   - Request ID
   - Current status
   - User's issue description
3. **Action Buttons**:
   - **Open Chat**: Opens the chat interface with the user
   - **Solve**: Marks the request as solved (prompts for solution details)

### Workflow

1. **Admin** types `/panel` in the admin group
2. The **Admin Panel WebApp** opens, showing all active requests
3. Admin can view request details and take actions:
   - **Open Chat**: Opens the chat interface to communicate with the user
   - **Solve**: Initiates the solution flow to mark the request as solved

## Technical Implementation

### Module Structure

```
app/admin_panel/
├── __init__.py         # Module initialization and exports
├── config.py           # Configuration settings and utilities
└── handlers.py         # Command handlers for the admin panel
```

```
webapp-support-bot/
└── admin-panel.html    # WebApp frontend interface
```

### API Endpoints

The following API endpoints support the Admin Panel functionality:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/support/requests` | GET | Retrieves a list of support requests with optional filtering by status |
| `/api/support/requests/{request_id}/solve` | POST | Marks a request as solved |

### Integration

The Admin Panel module integrates with the core bot through:

1. **Command Registration**: The `/panel` command is registered when the module is enabled
2. **WebApp Interface**: Uses Telegram's WebApp functionality to display the interface
3. **API Endpoints**: Dedicated endpoints for retrieving and manipulating request data

## Decoupling

The Admin Panel module is designed to be completely decoupled from the core functionality:

1. **Feature Flag**: Can be disabled via environment variable without affecting other features
2. **Isolated Code**: All functionality is contained within the `app/admin_panel` directory
3. **Conditional Registration**: Command handlers are only registered when the module is enabled
4. **Graceful Degradation**: When disabled, appropriate messages are shown to administrators

To completely remove the module:

1. Set `ADMIN_PANEL_ENABLED=false` in your `.env` file
2. The module will be effectively disabled without the need to remove any code
3. For a physical removal, you can delete the `app/admin_panel` directory and related WebApp files

## Security Considerations

1. **Admin-only Access**: The panel is only accessible to administrators via the admin group
2. **API Protection**: API endpoints check if the admin panel is enabled before processing requests
3. **Data Validation**: All inputs are validated before processing

## Extending the Admin Panel

The Admin Panel module can be extended with additional features:

1. Add new API endpoints in `app/api/routes/admin.py`
2. Update the WebApp interface in `webapp-support-bot/admin-panel.html`
3. Add new command handlers in `app/admin_panel/handlers.py`

## Troubleshooting

### Common Issues

1. **Admin Panel not appearing**: Ensure `ADMIN_PANEL_ENABLED=true` in your `.env` file
2. **Empty request list**: Check database connection and that there are open requests
3. **WebApp errors**: Check browser console for JavaScript errors

### Debugging

1. Check the bot logs for any errors related to the admin panel
2. Verify that the API endpoints are working correctly
3. Ensure the WebApp is properly deployed and accessible

## Conclusion

The Admin Panel module provides a convenient interface for administrators to manage support requests. Its modular design allows it to be enabled, disabled, or modified without affecting the core functionality of the Support Bot. 
# Admin Workflows

This document outlines the common workflows for admins when handling support requests in the Support Bot system.

## Overview

Admins are responsible for reviewing and resolving support requests submitted by users. The Support Bot provides a streamlined workflow for managing these requests efficiently.

## Support Request Lifecycle

A support request typically follows this lifecycle:

1. **Created** - User submits a new support request
2. **Assigned** - An admin takes ownership of the request
3. **In Progress** - Admin communicates with the user to understand and address the issue
4. **Resolved** - Admin marks the request as solved with a solution description
5. **Closed** - Request is archived (automatic after resolution)

## Admin Notification

When a user submits a new support request:

1. The admin group receives a notification with:
   - Request ID
   - User ID
   - Brief preview of the issue
   - Two action buttons: "Open Chat" and "Solve"

Example notification:
```
🆕 New support request #42
👤 User ID: 123456789
📝 Issue: I need help with setting up the bot...

[Open Chat] [Solve]
```

## Assigning Requests

Requests are automatically assigned to the admin who clicks the "Open Chat" button. When this happens:

1. The request status changes to "assigned"
2. A system message is added to the chat indicating the assignment
3. The admin group notification is updated to show who's handling the request

## Chat Interface

When an admin clicks "Open Chat":

1. The admin receives a private message with a link to the chat interface
2. The chat interface shows the entire conversation history
3. The admin can send messages that the user will see in real-time

## Resolving Requests

When an admin is ready to resolve a request, they can follow this workflow:

1. Click the "Solve" button in the admin group
2. The bot will send a private message asking for solution details
3. Admin enters a detailed solution text
4. The bot processes the solution and:
   - Marks the request as "solved" in the database
   - Stores the solution text with the request
   - Sends a notification to the user with the solution
   - Updates the admin group with the resolution status

Example solution flow:

**Admin clicks "Solve" button in group**

Bot to admin (private chat):
```
Please provide a brief description of the solution for request #42:
```

**Admin enters solution**:
```
Reset the user's API key and provided instructions on how to update their configuration file.
```

**Bot to user**:
```
✅ Your support request (#42) has been resolved.

📝 Solution: Reset the user's API key and provided instructions on how to update their configuration file.

Thank you for using our support service!
```

**Bot to admin group**:
```
✅ Request #42 resolved by Admin Name

📝 Solution: Reset the user's API key and provided instructions on how to update their configuration file.
```

## Best Practices for Admins

1. **Respond promptly** to new support requests
2. **Document clearly** when resolving requests
3. **Be specific** in solution descriptions
4. **Verify** that the user's issue is fully resolved before marking as solved
5. **Use consistent language** in solutions for similar issues
6. **Monitor** the admin group for new requests and updates

## Admin Commands

These commands are available to admins in the bot:

- `/requests` - Lists all open support requests
- `/view_[id]` - Shows details of a specific request
- `/help` - Shows available commands and usage

## Troubleshooting Admin Actions

If you encounter issues with admin actions:

1. **Button not responding**: Ensure the bot is running and check the logs for errors
2. **Chat link not working**: Verify the WebApp URL in your environment settings
3. **Cannot resolve request**: Check if you have the correct permissions
4. **Solution message not sending**: Check bot logs for error messages

For technical issues, refer to the [Troubleshooting](TROUBLESHOOTING.md) guide. 
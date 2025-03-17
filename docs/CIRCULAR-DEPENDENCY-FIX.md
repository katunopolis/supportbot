# Circular Dependency Resolution

This document outlines the approach taken to resolve circular import dependencies in the Support Bot application.

## Overview

Circular dependencies occur when two or more modules depend on each other, either directly or indirectly. These dependencies can cause problems during application initialization and result in partially initialized modules.

## Problem Identified

The following circular dependencies were identified in the codebase:

```
app/api/routes/support.py → app/bot/handlers/support.py → app/bot/bot.py → app/bot/handlers/support.py
```

This circular dependency caused issues during application startup, leading to import errors such as:

```
ImportError: cannot import name 'collect_issue' from partially initialized module 'app.bot.handlers.support' (most likely due to a circular import)
```

## Resolution Strategy

The circular dependency was resolved using the following techniques:

### 1. Delayed Imports

Instead of importing modules at the top level, imports were moved inside functions to delay them until actually needed:

**Before:**
```python
from app.bot.bot import bot

async def notify_admin_group(request_id: int, user_id: int, issue_text: str):
    # Function implementation using bot...
```

**After:**
```python
async def notify_admin_group(request_id: int, user_id: int, issue_text: str):
    # Import bot inside function to avoid circular import
    from app.bot.bot import bot
    
    # Function implementation using bot...
```

### 2. Restructured Imports

In bot.py, the import of `collect_issue` was moved from the top level to inside the function that uses it:

**Before:**
```python
from app.bot.handlers.support import collect_issue

async def handle_message(update: Update, context):
    # Function implementation using collect_issue...
```

**After:**
```python
async def handle_message(update: Update, context):
    # Import collect_issue here to avoid circular imports
    from app.bot.handlers.support import collect_issue
    
    # Function implementation using collect_issue...
```

### 3. Removed Unnecessary Imports

Unnecessary imports that contributed to the circular dependency chain were identified and removed.

### 4. Module Restructuring

When necessary, functionality was moved or split to avoid circular dependencies:

- Bot initialization was kept in `bot.py`
- Message handling was kept in `handlers/support.py`
- API endpoints were isolated in their respective route files

## Changes Made

Changes were made to the following files:

1. **app/bot/bot.py**:
   - Removed direct import of `collect_issue`
   - Added delayed import in the `handle_message` function

2. **app/bot/handlers/support.py**:
   - Removed direct import of `bot`
   - Added delayed import in the `notify_admin_group` function
   - Reorganized function structure to minimize dependencies

3. **app/api/routes/support.py**:
   - Used background tasks with delayed imports

4. **app/main.py**:
   - Reorganized imports to avoid circular dependencies
   - Removed unnecessary imports

## Best Practices for Avoiding Circular Dependencies

1. **Use Delayed Imports**: Import modules inside functions when they're needed
2. **Apply Dependency Injection**: Pass dependencies as parameters rather than importing them
3. **Create Interface Modules**: Create intermediate modules that both dependent modules can import
4. **Restructure Code**: Sometimes, moving functionality to different modules is the best solution
5. **Use Type Hints with Forward References**: Use string type hints to refer to types without importing them

## Testing

After implementing these changes, the application successfully starts without import errors, and all functionality related to the previously circular-dependent modules works as expected. 
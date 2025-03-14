# Support Bot Development Notes

## Project Structure
- `support-bot/`: Main bot implementation
  - `supportbot.py`: Core bot functionality and API endpoints
- `webapp-support-bot/`: Web application
  - `index.html`: Support request form with comprehensive documentation
  - `chat.html`: Support chat interface
- Documentation:
  - `CHANGELOG.md`: Version history and changes
  - `README.md`: Development guidelines and documentation

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
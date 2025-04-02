# WebApp Theming Guidelines

This document outlines the guidelines for proper theming in Telegram WebApp interfaces for the Support Bot.

## Overview

Telegram WebApp provides a built-in theming system that allows interfaces to adapt to the user's Telegram theme settings. This ensures a consistent and native-looking experience within the Telegram app.

## Theme Parameters

Telegram WebApp exposes theme colors through the `window.Telegram.WebApp.themeParams` object, which contains the following properties:

| Parameter | Description |
|-----------|-------------|
| `bg_color` | Background color |
| `text_color` | Main text color |
| `hint_color` | Hint text color (secondary text) |
| `link_color` | Link color |
| `button_color` | Button background color |
| `button_text_color` | Button text color |
| `secondary_bg_color` | Secondary background color |

## Correct Implementation

### 1. Initialize Theme Variables

Always use the `themeParams` object to set CSS variables that can be used throughout your interface:

```javascript
const tg = window.Telegram.WebApp;

// Initialize Telegram WebApp
tg.expand();
tg.ready();

// Access Telegram theme colors directly
const setThemeColors = () => {
    // Standard Telegram theme params
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color);
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color);
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color);
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color);
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color);
};

// Set theme colors and update if/when they change
setThemeColors();
tg.onEvent('themeChanged', setThemeColors);
```

### 2. CSS Usage

In your CSS, reference these variables:

```css
body {
    background-color: var(--tg-theme-bg-color);
    color: var(--tg-theme-text-color);
}

.button {
    background-color: var(--tg-theme-button-color);
    color: var(--tg-theme-button-text-color);
}

.hint-text {
    color: var(--tg-theme-hint-color);
}

.secondary-container {
    background-color: var(--tg-theme-secondary-bg-color);
}
```

## Common Mistakes to Avoid

### 1. Using Deprecated Properties

❌ **Incorrect:**
```javascript
// DEPRECATED - Do not use these properties directly
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.backgroundColor);
document.documentElement.style.setProperty('--tg-theme-text-color', tg.textColor);
```

✅ **Correct:**
```javascript
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
```

### 2. Using Hardcoded Fallback Colors

❌ **Incorrect:**
```javascript
// Do not use hardcoded fallback colors
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
```

✅ **Correct:**
```javascript
// Let Telegram provide the colors
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
```

### 3. Not Handling Theme Changes

❌ **Incorrect:**
```javascript
// Only set colors once at initialization
setThemeColors();
```

✅ **Correct:**
```javascript
// Set initially and listen for changes
setThemeColors();
tg.onEvent('themeChanged', setThemeColors);
```

### 4. Using Hardcoded Colors in CSS

❌ **Incorrect:**
```css
:root {
    --tg-theme-bg-color: #ffffff;
    --tg-theme-text-color: #000000;
}
```

✅ **Correct:**
```css
/* No hardcoded colors in :root */
/* Let JavaScript set these variables from tg.themeParams */
```

## Theme-Related HTML Meta Tags

Avoid using theme-color meta tags as they can conflict with Telegram's theming:

❌ **Incorrect:**
```html
<meta name="theme-color" content="#2481cc">
```

✅ **Correct:**
```html
<!-- No theme-color meta tags - let Telegram handle theming -->
```

## Time and Timezone Considerations

When implementing WebApps that display timestamps (like chat interfaces), ensure proper timezone handling:

### 1. Use ISO 8601 Timestamps with UTC

Always use ISO 8601 format with UTC time (Z suffix) for data exchange:

✅ **Correct:**
```javascript
// Get current timestamp in ISO 8601 format with UTC
function getCurrentTimestamp() {
    return new Date().toISOString();
}
```

### 2. Implement Client-Server Time Synchronization

Check for time differences between client and server clocks:

```javascript
// Synchronize with server time
function syncTimeWithServer(clientTime, serverTime) {
    const clientDate = new Date(clientTime);
    const serverDate = new Date(serverTime);
    
    // Calculate time difference
    const serverTimeOffset = serverDate.getTime() - clientDate.getTime();
    console.log(`Server time difference: ${serverTimeOffset}ms`);
    
    // Show indicator if significant difference exists
    if (Math.abs(serverTimeOffset) > 60000) { // More than a minute
        showTimeDifferenceIndicator(serverTimeOffset);
    }
}
```

### 3. Adapt Display to User's Local Timezone

Always display times in the user's local timezone:

```javascript
// Format date for display in user's local timezone
function formatDateForDisplay(isoString) {
    const date = new Date(isoString);
    
    // Format with options appropriate for your app
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}
```

### 4. Provide Context for Timestamps

For clearer user experience, show additional context for timestamps:

```javascript
// Format with appropriate context
function formatMessageTime(isoString) {
    const date = new Date(isoString);
    const today = new Date();
    const isToday = date.getDate() === today.getDate() && 
                    date.getMonth() === today.getMonth() && 
                    date.getFullYear() === today.getFullYear();
    
    if (isToday) {
        // Just show time for today's messages
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
        // Show date and time for older messages
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + 
               ' ' + 
               date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}
```

This approach ensures consistent timestamp display that adapts to users in different timezones while maintaining a harmonious appearance with Telegram's theming system.

## Testing Themes

To test your WebApp under different theme conditions:

1. Test in Telegram's light mode
2. Test in Telegram's dark mode
3. Test with custom Telegram themes

For comprehensive guidance on building WebApps for Telegram, refer to the [official Telegram WebApp documentation](https://core.telegram.org/bots/webapps). 
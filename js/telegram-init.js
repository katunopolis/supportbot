// Telegram initialization and theme setup
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Access Telegram theme colors directly
export const setThemeColors = () => {
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

// Export Telegram object for use in other modules
export default tg;

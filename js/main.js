import tg from './telegram-init.js';
import { initialize } from './chat-controller.js';

// Expose some global objects for backward compatibility
window.tg = tg;

// Initialize the application when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initialize();
});

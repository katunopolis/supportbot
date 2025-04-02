import { formatTimestamp, formatDateForDisplay } from "./time-utils.js";

// DOM element references will be initialized later
let chatContainer = null;
let messagesContainer = null;
let errorMessageElement = null;

/**
 * Initialize UI references
 */
export function initializeUI() {
    chatContainer = document.getElementById("chatContainer");
    messagesContainer = document.getElementById("messagesContainer");
    errorMessageElement = document.getElementById("errorMessage");
}

/**
 * Add a message to the UI
 * @param {Object} message - Message object
 * @returns {boolean} True if message was added, false if it was a duplicate
 */
export function addMessage(message) {
    // Don't process duplicate messages (check by id if available)
    if (message.id) {
        const existingMsg = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMsg) {
            console.log(`Message ID ${message.id} already exists, skipping`);
            return false;
        }
    }
    
    const isAdmin = message.sender_type === "admin";
    const isUser = message.sender_type === "user";
    const isSystem = message.sender_type === "system";
    const isMine = message.sender_id.toString() === window.currentUserId.toString();
    
    console.log("DEBUG: Rendering message:", {
        id: message.id || "no-id",
        isAdmin: isAdmin,
        isUser: isUser,
        isSystem: isSystem,
        isMine: isMine,
        sender_id: message.sender_id,
        currentUserId: window.currentUserId,
        sender_type: message.sender_type,
        timestamp: message.timestamp,
        message: message.message.substring(0, 30) + (message.message.length > 30 ? "..." : "")
    });

    // Create message div
    const messageDiv = document.createElement("div");
    
    if (isSystem) {
        messageDiv.className = "message system";
    } else {
        // Apply appropriate classes
        messageDiv.className = `message ${isAdmin ? "admin" : "user"} ${isMine ? "my-message" : ""}`;
    }
    
    // Add message ID as data attribute if available
    if (message.id) {
        messageDiv.setAttribute("data-message-id", message.id);
    }

    // Ensure ISO timestamp for display
    const timestamp = formatTimestamp(message.timestamp);
    const displayTime = formatDateForDisplay(timestamp);
    
    // For debugging purposes, also show the UTC time if there's a significant difference
    const date = new Date(timestamp);
    const utcHours = date.getUTCHours().toString().padStart(2, "0");
    const utcMinutes = date.getUTCMinutes().toString().padStart(2, "0");
    const utcTimeString = `${utcHours}:${utcMinutes}`;
    
    // Check if local time and UTC time are different
    const localHours = date.getHours().toString().padStart(2, "0");
    const localMinutes = date.getMinutes().toString().padStart(2, "0");
    const localTimeString = `${localHours}:${localMinutes}`;
    
    // Determine if we need to show both times for clarity
    const showBothTimes = localTimeString !== utcTimeString;
    const timeDisplay = showBothTimes ? 
        `${displayTime} (UTC: ${utcTimeString})` : 
        displayTime;
    
    // Create ISO8601 date attribute for sorting and comparison
    messageDiv.setAttribute("data-timestamp", timestamp);

    try {
        // Add sender identifier for clarity when user and admin are chatting
        let senderLabel = "Unknown";
        if (isAdmin) senderLabel = "Admin";
        else if (isUser) senderLabel = "User";
        else if (isSystem) senderLabel = "System";
        
        if (isSystem) {
            messageDiv.innerHTML = `
                <div class="message-content">${escapeHtml(message.message)}</div>
                <div class="message-time">${timeDisplay}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-sender">${isMine ? "You" : senderLabel} (${message.sender_id})</div>
                <div class="message-content">${escapeHtml(message.message)}</div>
                <div class="message-time">${timeDisplay}</div>
                <div class="message-timestamp" style="display: none;">${timestamp}</div>
            `;
        }
    } catch (e) {
        console.error("Error creating message element:", e);
        // Simple fallback
        messageDiv.innerHTML = `<div class="message-content">${escapeHtml(message.message)}</div>`;
    }

    messagesContainer.appendChild(messageDiv);
    console.log(`Message added to UI: ${message.sender_type} (${message.sender_id}): ${message.message.substring(0, 30)}... at ${timestamp}`);
    
    return true;
}

/**
 * Scroll chat container to bottom
 */
export function scrollToBottom() {
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

/**
 * Show error message
 * @param {string} message - Error message
 */
export function showError(message) {
    if (errorMessageElement) {
        errorMessageElement.textContent = message;
        errorMessageElement.style.display = "block";
        setTimeout(() => {
            errorMessageElement.style.display = "none";
        }, 5000);
    }
}

/**
 * Update request information in the UI
 * @param {Object} data - Request data
 */
export function updateRequestInfo(data) {
    const requestTitle = document.getElementById("requestTitle");
    const requestStatus = document.getElementById("requestStatus");
    
    if (requestTitle && data.request_id) {
        requestTitle.textContent = `Support Request #${data.request_id}`;
    }
    
    if (requestStatus && data.status) {
        requestStatus.textContent = `Status: ${data.status}`;
    }
}

/**
 * Adjust textarea height based on content
 * @param {HTMLElement} textarea - Textarea element
 */
export function adjustTextareaHeight(textarea) {
    if (textarea) {
        textarea.style.height = "auto";
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + "px";
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
export function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

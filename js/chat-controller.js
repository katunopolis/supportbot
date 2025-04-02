import { loadChatHistory, pollMessages, sendMessage, setLastMessageTimestamp } from "./chat-api.js";
import { initializeUI, addMessage, scrollToBottom, showError, updateRequestInfo, adjustTextareaHeight } from "./chat-ui.js";
import { getCurrentTimestamp, updateTimeDisplays } from "./time-utils.js";

// State variables
let isPolling = false;
let isInitializing = false;
let pollingInterval = null;
let requestId = null;

/**
 * Initialize the chat controller
 */
export function initialize() {
    // Initialize UI references
    initializeUI();
    
    // Get parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    window.adminIdFromQuery = urlParams.get("admin_id");
    requestId = urlParams.get("request_id");
    
    // Try to get request ID from path if not in query params
    if (!requestId) {
        const pathSegments = window.location.pathname.split("/");
        if (pathSegments.length > 2 && pathSegments[1] === "chat") {
            requestId = pathSegments[2];
        }
    }
    
    // Set up global variables for modules that need them
    window.currentUserId = window.adminIdFromQuery || (window.tg?.initDataUnsafe?.user?.id || "unknown");
    window.currentUserType = window.adminIdFromQuery ? "admin" : "user";
    
    console.log("Chat initialization:", {
        requestId: requestId,
        currentUserId: window.currentUserId,
        currentUserType: window.currentUserType,
        isAdmin: !!window.adminIdFromQuery
    });
    
    // Set up DOM event listeners
    setupEventListeners();
    
    // Start the chat
    loadChat(requestId);
    
    // Set up time display updating
    setInterval(updateTimeDisplays, 1000);
    updateTimeDisplays();
}

/**
 * Set up event listeners for the chat interface
 */
function setupEventListeners() {
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    
    if (messageInput) {
        messageInput.addEventListener("input", () => adjustTextareaHeight(messageInput));
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        });
    }
    
    if (sendButton) {
        sendButton.addEventListener("click", sendUserMessage);
    }
    
    // Handle page visibility changes
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            console.debug("Page hidden, stopping polling");
            stopPolling();
        } else {
            console.debug("Page visible, restarting chat");
            loadChat(requestId); // Reload chat history when page becomes visible again
        }
    });
    
    // Cleanup on page unload
    window.addEventListener("unload", () => {
        console.debug("Page unloading, stopping polling");
        stopPolling();
    });
}

/**
 * Load the chat history and start polling
 * @param {string|number} requestId - Request ID
 */
async function loadChat(requestId) {
    if (!requestId) {
        showError("No request ID provided");
        return;
    }
    
    if (isInitializing || isPolling) {
        console.warn("Already initializing or polling, skipping loadChat");
        return;
    }

    isInitializing = true;
    try {
        const data = await loadChatHistory(requestId);
        
        // Update UI with chat data
        updateRequestInfo(data);
        
        // Add messages to UI
        const messagesContainer = document.getElementById("messagesContainer");
        if (messagesContainer) {
            messagesContainer.innerHTML = "";
            
            if (data.messages && data.messages.length > 0) {
                console.log(`Loaded ${data.messages.length} messages from history`);
                
                data.messages.forEach(msg => {
                    console.log("Adding message from history:", {
                        id: msg.id || "no-id",
                        sender_id: msg.sender_id,
                        sender_type: msg.sender_type,
                        message: msg.message.substring(0, 30) + (msg.message.length > 30 ? "..." : ""),
                        timestamp: msg.timestamp,
                        isMine: msg.sender_id.toString() === window.currentUserId.toString()
                    });
                    addMessage(msg);
                });
                
                // Set the last message timestamp for polling
                if (data.messages.length > 0) {
                    setLastMessageTimestamp(data.messages[data.messages.length - 1].timestamp);
                    console.log("Setting last message timestamp");
                } else {
                    setLastMessageTimestamp(getCurrentTimestamp());
                }
            } else {
                console.log("No messages in history, using current time as lastMessageTimestamp");
                setLastMessageTimestamp(getCurrentTimestamp());
            }
        }
        
        // Start polling only if not already polling
        if (!isPolling) {
            startPolling(requestId);
        }
        
        // Scroll to bottom
        scrollToBottom();
    } catch (error) {
        console.error("Error loading chat:", error);
        showError("Failed to load chat history. Please try refreshing.");
        // Ensure we have a valid timestamp even on error
        setLastMessageTimestamp(getCurrentTimestamp());
    } finally {
        isInitializing = false;
    }
}

/**
 * Start polling for new messages
 * @param {string|number} requestId - Request ID
 */
function startPolling(requestId) {
    if (isPolling) {
        console.warn("Already polling, skipping startPolling");
        return;
    }
    
    stopPolling(); // Clean up any existing interval
    
    isPolling = true;
    let retryCount = 0;
    const maxRetryDelay = 5000;
    const baseDelay = 1000;
    
    async function doPoll() {
        // Skip if we're initializing or if polling has been stopped
        if (isInitializing || !isPolling) {
            return;
        }

        try {
            const hasNewMessages = await pollMessages(requestId, (message) => {
                // Add each new message to the UI
                addMessage(message);
            });
            
            if (hasNewMessages) {
                scrollToBottom();
            }
            
            retryCount = 0; // Reset retry count on success
        } catch (error) {
            console.error("Error polling messages:", error);
            retryCount++;
            
            if (retryCount > 3) {
                console.warn("Too many polling errors, reloading chat history");
                stopPolling();
                setTimeout(() => {
                    loadChat(requestId); // Reload chat history after a brief pause
                }, 1000);
                return;
            }
            
            // Back off exponentially on errors
            const delay = Math.min(baseDelay * Math.pow(2, retryCount), maxRetryDelay);
            clearInterval(pollingInterval);
            if (isPolling) { // Only set new interval if still polling
                console.log(`Polling retry in ${delay}ms (attempt ${retryCount})`);
                pollingInterval = setInterval(doPoll, delay);
            }
        }
    }

    pollingInterval = setInterval(doPoll, baseDelay);
    console.log(`Started polling with interval ${baseDelay}ms`);
    doPoll(); // Initial poll
}

/**
 * Stop polling for new messages
 */
function stopPolling() {
    console.debug("Stopping polling");
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
    isPolling = false;
}

/**
 * Send a message from the user
 */
async function sendUserMessage() {
    const messageInput = document.getElementById("messageInput");
    if (!messageInput) return;
    
    const text = messageInput.value.trim();
    if (!text) return;

    messageInput.value = "";
    adjustTextareaHeight(messageInput);

    try {
        // Create message object
        const messageData = {
            sender_id: window.currentUserId,
            sender_type: window.currentUserType,
            message: text,
            timestamp: getCurrentTimestamp()
        };

        // Add message to UI immediately (optimistic update)
        addMessage(messageData);
        scrollToBottom();

        // Send message to server
        await sendMessage(
            requestId,
            text,
            window.currentUserId,
            window.currentUserType
        );
    } catch (error) {
        console.error("Error sending message:", error);
        showError("Failed to send message. Please try again.");
    }
}

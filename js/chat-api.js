import { syncTimeWithServer, formatTimestamp, getCurrentTimestamp, isNewerTimestamp } from "./time-utils.js";

// Initialize variables
const API_BASE_URL = window.location.hostname === "localhost" ? "http://localhost:8000" : "";
let lastMessageTimestamp = null;

/**
 * Load chat history with fallback mechanisms
 * @param {number} requestId - Request ID
 * @returns {Promise<Object>} Chat data
 */
export async function loadChatHistory(requestId) {
    const endpoints = [
        `${API_BASE_URL}/api/chat/${requestId}`,
        `${API_BASE_URL}/api/support/chat/${requestId}`,
        `${API_BASE_URL}/admin-chat-direct/${requestId}/${window.adminIdFromQuery}`,
        `${API_BASE_URL}/direct-admin-chat/${requestId}/${window.adminIdFromQuery}`
    ];

    let response;
    let successEndpoint;
    for (const endpoint of endpoints) {
        try {
            console.log(`Trying to load chat history from: ${endpoint}`);
            const clientTime = new Date().toISOString();
            const resp = await fetch(endpoint, {
                headers: {
                    "Cache-Control": "no-cache",
                    "X-Client-Timezone": Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
                    "X-Client-Time": clientTime
                }
            });
            if (resp.ok) {
                // Get server time if available in response headers
                const serverTime = resp.headers.get("X-Server-Time");
                if (serverTime) {
                    syncTimeWithServer(clientTime, serverTime);
                }
                
                response = resp;
                successEndpoint = endpoint;
                break;
            }
        } catch (e) {
            console.warn(`Failed to fetch from ${endpoint}:`, e);
        }
    }

    if (!response?.ok) {
        throw new Error("Failed to load chat history from any endpoint");
    }

    console.log(`Successfully loaded chat history from: ${successEndpoint}`);
    const data = await response.json();
    
    // Synchronize with server time if provided in response
    if (data.server_time) {
        const clientTime = new Date().toISOString();
        syncTimeWithServer(clientTime, data.server_time);
    }
    
    // Standardize all timestamps to ISO 8601 format
    if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => {
            if (msg.timestamp) {
                msg.timestamp = formatTimestamp(msg.timestamp);
            } else {
                console.warn(`Message ID ${msg.id || "unknown"} has no timestamp, using current time`);
                msg.timestamp = getCurrentTimestamp();
            }
        });
        
        // Sort messages by timestamp to ensure correct order
        data.messages.sort((a, b) => {
            try {
                const timeA = new Date(a.timestamp).getTime();
                const timeB = new Date(b.timestamp).getTime();
                return timeA - timeB;
            } catch (e) {
                console.error("Error sorting messages by timestamp:", e);
                return 0;
            }
        });
        
        // Set the last message timestamp for polling
        if (data.messages.length > 0) {
            lastMessageTimestamp = formatTimestamp(data.messages[data.messages.length - 1].timestamp);
        }
    }
    
    return data;
}

/**
 * Poll for new messages
 * @param {number} requestId - Request ID
 * @param {function} messageHandler - Function to handle new messages
 */
export async function pollMessages(requestId, messageHandler) {
    try {
        const timestamp = formatTimestamp(lastMessageTimestamp);
        console.debug(`Polling for new messages since ${timestamp}`);

        // Try multiple endpoints for better reliability
        const endpoints = [
            `${API_BASE_URL}/api/chat/${requestId}/messages?since=${encodeURIComponent(timestamp)}`,
            `${API_BASE_URL}/api/support/chat/${requestId}/messages?since=${encodeURIComponent(timestamp)}`
        ];
        
        // If we're an admin, add admin-specific endpoints
        if (window.adminIdFromQuery) {
            endpoints.push(`${API_BASE_URL}/admin-chat-direct/${requestId}/${window.adminIdFromQuery}/messages?since=${encodeURIComponent(timestamp)}`);
        }

        let response = null;
        let successEndpoint = null;
        
        // Try each endpoint until one succeeds
        for (const endpoint of endpoints) {
            try {
                console.debug(`Trying endpoint: ${endpoint}`);
                
                const resp = await fetch(endpoint, {
                    headers: {
                        "Cache-Control": "no-cache",
                        "X-Last-Timestamp": timestamp,
                        "X-User-ID": window.currentUserId,
                        "X-User-Type": window.currentUserType
                    }
                });
                
                if (resp.ok) {
                    response = resp;
                    successEndpoint = endpoint;
                    break;
                }
            } catch (endpointError) {
                console.warn(`Failed to poll from ${endpoint}:`, endpointError);
            }
        }

        if (!response) {
            throw new Error("All polling endpoints failed");
        }

        const messages = await response.json();
        console.log(`Received ${messages.length} messages in polling from ${successEndpoint}`);
        
        if (messages && messages.length > 0) {
            let hasNewMessages = false;
            
            messages.forEach(msg => {
                const msgTimestamp = formatTimestamp(msg.timestamp);
                
                if (isNewerTimestamp(msgTimestamp, lastMessageTimestamp)) {
                    msg.timestamp = msgTimestamp;
                    messageHandler(msg);
                    lastMessageTimestamp = msgTimestamp;
                    hasNewMessages = true;
                } else {
                    console.log("Skipping older message:", msgTimestamp, "<", lastMessageTimestamp);
                }
            });
            
            return hasNewMessages;
        }
        
        return false;
    } catch (error) {
        console.error("Error polling messages:", error);
        throw error;
    }
}

/**
 * Send a new message
 * @param {number} requestId - Request ID
 * @param {string} text - Message text
 * @param {number} senderId - Sender ID
 * @param {string} senderType - Sender type ('user' or 'admin')
 * @returns {Promise<Object>} Message data
 */
export async function sendMessage(requestId, text, senderId, senderType) {
    // Generate ISO 8601 UTC timestamp, adjusted for any server time difference
    const currentTimestamp = getCurrentTimestamp();

    const messageData = {
        sender_id: senderId,
        sender_type: senderType,
        message: text,
        timestamp: currentTimestamp
    };

    console.log("Sending message:", {
        ...messageData,
        message_truncated: text.substring(0, 30) + (text.length > 30 ? "..." : "")
    });

    // Send to server
    console.log(`Sending to ${API_BASE_URL}/api/chat/${requestId}/messages with timestamp ${currentTimestamp}`);
    const response = await fetch(`${API_BASE_URL}/api/chat/${requestId}/messages`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Client-Timestamp": currentTimestamp,
            "X-Timezone-Offset": new Date().getTimezoneOffset(),
            "X-Client-Time-Ms": new Date().getTime().toString() // Send milliseconds since epoch for more precise time sync
        },
        body: JSON.stringify(messageData)
    });

    if (!response.ok) {
        console.error(`Server error: ${response.status} ${response.statusText}`);
        const errorText = await response.text();
        console.error(`Error details: ${errorText}`);
        throw new Error(`Failed to send message: ${response.status}`);
    }

    const data = await response.json();
    
    // Get server time if available in response headers
    const serverTime = response.headers.get("X-Server-Time");
    if (serverTime) {
        syncTimeWithServer(currentTimestamp, serverTime);
    }
    
    // Update the timestamp from the server response or fall back to the client timestamp
    if (data.timestamp) {
        // Use server timestamp for better synchronization
        lastMessageTimestamp = formatTimestamp(data.timestamp);
    } else {
        // Fall back to client timestamp if server doesn't provide one
        lastMessageTimestamp = currentTimestamp;
    }
    
    return {
        ...messageData,
        id: data.id || null
    };
}

/**
 * Get the last message timestamp
 * @returns {string} Last message timestamp
 */
export function getLastMessageTimestamp() {
    return lastMessageTimestamp;
}

/**
 * Set the last message timestamp
 * @param {string} timestamp - Timestamp to set
 */
export function setLastMessageTimestamp(timestamp) {
    lastMessageTimestamp = formatTimestamp(timestamp);
}

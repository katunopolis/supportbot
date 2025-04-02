// Initialize server time offset
let serverTimeOffset = 0; // Time difference between server and client in milliseconds

/**
 * Synchronize client time with server time to account for differences
 * @param {string} clientTime - ISO timestamp from client
 * @param {string} serverTime - ISO timestamp from server
 */
export function syncTimeWithServer(clientTime, serverTime) {
    try {
        const clientDate = new Date(clientTime);
        const serverDate = new Date(serverTime);
        
        if (isNaN(clientDate.getTime()) || isNaN(serverDate.getTime())) {
            throw new Error("Invalid date format");
        }
        
        // Calculate time difference in milliseconds
        serverTimeOffset = serverDate.getTime() - clientDate.getTime();
        console.log(`Time sync: Server time is ${serverTimeOffset > 0 ? "ahead by" : "behind by"} ${Math.abs(serverTimeOffset) / 1000} seconds`);
        
        // Update the time difference indicator if significant
        const timeDifferenceMinutes = Math.round(Math.abs(serverTimeOffset) / 60000);
        if (Math.abs(serverTimeOffset) > 60000) { // More than a minute difference
            console.warn(`⚠️ Large time difference detected: ${serverTimeOffset / 1000} seconds!`);
            updateTimeDifferenceIndicator(timeDifferenceMinutes, serverTimeOffset > 0);
        } else {
            hideTimeDifferenceIndicator();
        }
    } catch (e) {
        console.error("Error synchronizing time with server:", e);
    }
}

/**
 * Update the time difference indicator in the UI
 * @param {number} minutesDifference - Time difference in minutes
 * @param {boolean} isServerAhead - Whether server is ahead of client
 */
export function updateTimeDifferenceIndicator(minutesDifference, isServerAhead) {
    // Create or get the time difference indicator
    let indicator = document.getElementById("timeDifferenceIndicator");
    if (!indicator) {
        indicator = document.createElement("div");
        indicator.id = "timeDifferenceIndicator";
        indicator.className = "time-difference-indicator";
        document.getElementById("chatHeader").appendChild(indicator);
    }
    
    // Set the message based on the time difference
    const direction = isServerAhead ? "ahead of" : "behind";
    indicator.textContent = `Server time is ${minutesDifference} minute${minutesDifference !== 1 ? "s" : ""} ${direction} your local time`;
    indicator.style.display = "block";
}

/**
 * Hide the time difference indicator when not needed
 */
export function hideTimeDifferenceIndicator() {
    const indicator = document.getElementById("timeDifferenceIndicator");
    if (indicator) {
        indicator.style.display = "none";
    }
}

/**
 * Get current timestamp adjusted for server time if needed
 * @returns {string} ISO timestamp
 */
export function getCurrentTimestamp() {
    const now = new Date();
    
    // If we have a significant server time offset, adjust the timestamp
    if (Math.abs(serverTimeOffset) > 5000) { // Only adjust if offset is more than 5 seconds
        const serverAdjustedTime = new Date(now.getTime() + serverTimeOffset);
        console.debug(`Time adjusted for server offset: 
            - Client time: ${now.toISOString()}
            - Server adjusted: ${serverAdjustedTime.toISOString()} 
            - Offset: ${serverTimeOffset}ms`);
        return serverAdjustedTime.toISOString();
    }
    
    console.debug(`Current time (ISO): ${now.toISOString()}`);
    return now.toISOString();
}

/**
 * Format timestamp consistently according to ISO 8601
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} Formatted ISO timestamp
 */
export function formatTimestamp(timestamp) {
    if (!timestamp) {
        console.warn("Empty timestamp provided, using current time");
        return getCurrentTimestamp();
    }
    
    try {
        // Handle different timestamp formats
        let date;
        if (typeof timestamp === "string") {
            // Handle Z suffix (UTC) or timezone offset
            if (timestamp.endsWith("Z")) {
                date = new Date(timestamp);
            } else if (timestamp.includes("+") || timestamp.includes("-")) {
                // Already has timezone information
                date = new Date(timestamp);
            } else {
                // Assume UTC if no timezone info
                date = new Date(timestamp + "Z");
            }
            
            // Check if the date is valid
            if (isNaN(date.getTime())) {
                throw new Error("Invalid date from string timestamp: " + timestamp);
            }
        } else if (timestamp instanceof Date) {
            date = timestamp;
        } else {
            throw new Error("Unsupported timestamp format: " + typeof timestamp);
        }
        
        // Format as ISO string and ensure UTC (Z)
        return date.toISOString();
    } catch (e) {
        console.error("Error formatting timestamp:", e, timestamp);
        return getCurrentTimestamp();
    }
}

/**
 * Format date for display in messages with proper timezone handling
 * @param {string} isoString - ISO timestamp
 * @returns {string} Formatted time for display
 */
export function formatDateForDisplay(isoString) {
    try {
        // Parse the ISO string (which is in UTC format)
        const date = new Date(isoString);
        
        // Check if the date is valid
        if (isNaN(date.getTime())) {
            throw new Error("Invalid date for display formatting: " + isoString);
        }
        
        // Get user's timezone info for debugging
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const offsetMinutes = -new Date().getTimezoneOffset(); // Negative because getTimezoneOffset returns opposite sign
        const offsetHours = offsetMinutes / 60;
        
        // Log timezone debugging info with additional server time offset information
        console.debug(`Formatting time: 
            - ISO: ${isoString} 
            - User timezone: ${userTimezone} (UTC${offsetHours >= 0 ? "+" : ""}${offsetHours})
            - UTC time: ${date.getUTCHours()}:${date.getUTCMinutes()}
            - Local: ${date.getHours()}:${date.getMinutes()}
            - Server offset: ${serverTimeOffset}ms`);
        
        // Check if the message is from today
        const today = new Date();
        const isToday = date.getDate() === today.getDate() && 
                       date.getMonth() === today.getMonth() && 
                       date.getFullYear() === today.getFullYear();
        
        // Format time explicitly using local values to avoid issues with Intl.DateTimeFormat
        const hours = date.getHours().toString().padStart(2, "0");
        const minutes = date.getMinutes().toString().padStart(2, "0");
        const timeString = `${hours}:${minutes}`;
        
        // Format date parts if needed
        let formattedTime;
        if (isToday) {
            // Just show time for today's messages
            formattedTime = timeString;
        } else {
            // Show date and time for older messages
            const day = date.getDate().toString().padStart(2, "0");
            const month = (date.getMonth() + 1).toString().padStart(2, "0"); // getMonth() is 0-based
            formattedTime = `${day}/${month} ${timeString}`;
        }
        
        console.debug(`Final formatted time: ${formattedTime} (isToday: ${isToday})`);
        return formattedTime;
    } catch (e) {
        console.error("Error formatting date for display:", e, isoString);
        return "??:??";
    }
}

/**
 * Compare two ISO 8601 timestamps
 * @param {string} timestamp1 - First timestamp
 * @param {string} timestamp2 - Second timestamp
 * @returns {boolean} True if timestamp1 is newer than timestamp2
 */
export function isNewerTimestamp(timestamp1, timestamp2) {
    try {
        const date1 = new Date(timestamp1);
        const date2 = new Date(timestamp2);
        return date1.getTime() > date2.getTime();
    } catch (e) {
        console.error("Error comparing timestamps:", e);
        return false;
    }
}

/**
 * Update the time displays in the header
 */
export function updateTimeDisplays() {
    // Current client time
    const now = new Date();
    const clientHours = now.getHours().toString().padStart(2, "0");
    const clientMinutes = now.getMinutes().toString().padStart(2, "0");
    const clientSeconds = now.getSeconds().toString().padStart(2, "0");
    document.getElementById("clientTimeDisplay").textContent = `Local: ${clientHours}:${clientMinutes}:${clientSeconds}`;
    
    // Current server time (adjusted by offset)
    if (Math.abs(serverTimeOffset) > 0) {
        const serverTime = new Date(now.getTime() + serverTimeOffset);
        const serverHours = serverTime.getHours().toString().padStart(2, "0");
        const serverMinutes = serverTime.getMinutes().toString().padStart(2, "0");
        const serverSeconds = serverTime.getSeconds().toString().padStart(2, "0");
        document.getElementById("serverTimeDisplay").textContent = `Server: ${serverHours}:${serverMinutes}:${serverSeconds}`;
        document.getElementById("serverTimeDisplay").style.display = "inline";
    } else {
        document.getElementById("serverTimeDisplay").style.display = "none";
    }
}

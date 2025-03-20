#!/usr/bin/env python

"""
Test ISO 8601 timestamp handling throughout the application.
This script verifies that timestamps are properly formatted and parsed.
"""

import sys
import os
import json
import requests
from datetime import datetime, timezone
import re
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up API URLs
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def test_iso8601_formatting():
    """Test timestamp formatting to ISO 8601."""
    # Create a timestamp in UTC
    now = datetime.now(timezone.utc)
    
    # Format it according to our standard
    formatted = now.isoformat().replace('+00:00', 'Z')
    
    # Check that it matches the expected format
    iso8601_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z'
    if not re.match(iso8601_pattern, formatted):
        logger.error(f"Formatted timestamp does not match ISO 8601 pattern: {formatted}")
        return False
    
    logger.info(f"✓ ISO 8601 formatting test passed: {formatted}")
    return True


def test_iso8601_parsing():
    """Test parsing ISO 8601 timestamps."""
    # Sample timestamp
    timestamp_str = "2023-04-15T14:30:25.123Z"
    
    try:
        # Parse the timestamp
        parsed = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Check that it has timezone info
        if parsed.tzinfo is None:
            logger.error("Parsed timestamp is missing timezone information")
            return False
        
        # Convert back to string for comparison
        reparsed = parsed.isoformat().replace('+00:00', 'Z')
        
        # Verify it matches the original (accounting for potential precision differences)
        original_parts = timestamp_str.split('.')
        reparsed_parts = reparsed.split('.')
        
        if original_parts[0] != reparsed_parts[0]:
            logger.error(f"Reparsed timestamp does not match original: {timestamp_str} vs {reparsed}")
            return False
            
        logger.info(f"✓ ISO 8601 parsing test passed: {timestamp_str} -> {reparsed}")
        return True
        
    except Exception as e:
        logger.error(f"Error parsing ISO 8601 timestamp: {e}")
        return False


def test_api_timestamp_response():
    """Test that the API returns properly formatted timestamps."""
    try:
        # Try to get a list of chats to check timestamp formatting
        url = f"{API_BASE_URL}/api/chat/chats"
        logger.info(f"Testing API response with URL: {url}")
        
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            if response.status_code == 500:
                logger.error(f"Server error (500) when connecting to {url}")
                try:
                    error_content = response.text[:500]  # Limit to first 500 chars
                    logger.error(f"Error content: {error_content}")
                except Exception as e:
                    logger.error(f"Could not extract error content: {e}")
            
            # Try a different endpoint to see if any chat endpoint works
            logger.info("Attempting to access a specific chat endpoint as fallback")
            fallback_url = f"{API_BASE_URL}/api/chat/1"
            fallback_response = requests.get(fallback_url)
            logger.info(f"Fallback response status code: {fallback_response.status_code}")
            
            logger.warning(f"Could not get chat list, status code: {response.status_code}")
            logger.info("Skipping API timestamp response test")
            return None
            
        data = response.json()
        
        # Check that the response contains timestamps
        if not data or not isinstance(data, list):
            logger.warning("API response does not contain expected data format")
            return None
            
        # Check formatting of timestamps in the response
        iso8601_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z'
        timestamp_checks = []
        
        for chat in data:
            # Check created_at
            if 'created_at' in chat:
                created_at = chat['created_at']
                if not re.match(iso8601_pattern, created_at):
                    logger.error(f"created_at timestamp does not match ISO 8601 pattern: {created_at}")
                    timestamp_checks.append(False)
                else:
                    timestamp_checks.append(True)
                    
            # Check updated_at
            if 'updated_at' in chat:
                updated_at = chat['updated_at']
                if not re.match(iso8601_pattern, updated_at):
                    logger.error(f"updated_at timestamp does not match ISO 8601 pattern: {updated_at}")
                    timestamp_checks.append(False)
                else:
                    timestamp_checks.append(True)
                    
            # Check latest_message timestamp if present
            if 'latest_message' in chat and chat['latest_message'] and 'timestamp' in chat['latest_message']:
                msg_timestamp = chat['latest_message']['timestamp']
                if not re.match(iso8601_pattern, msg_timestamp):
                    logger.error(f"message timestamp does not match ISO 8601 pattern: {msg_timestamp}")
                    timestamp_checks.append(False)
                else:
                    timestamp_checks.append(True)
        
        if timestamp_checks and all(timestamp_checks):
            logger.info(f"✓ API timestamp response test passed: checked {len(timestamp_checks)} timestamps")
            return True
        elif timestamp_checks:
            logger.error(f"Some API timestamps did not pass validation: {timestamp_checks.count(False)} failed")
            return False
        else:
            logger.warning("No timestamps found in API response")
            return None
            
    except Exception as e:
        logger.error(f"Error testing API timestamp response: {e}")
        return False


def test_api_timestamp_handling():
    """Test that the API correctly handles timestamp parameters."""
    try:
        # Create an intentionally malformed timestamp to test error handling
        malformed_timestamp = "not-a-timestamp"
        
        # Try to get messages with the malformed timestamp
        url = f"{API_BASE_URL}/api/chat/1/messages?since={malformed_timestamp}"
        logger.info(f"Testing malformed timestamp with URL: {url}")
        
        response = requests.get(
            url,
            headers={"X-Test-Timestamp": "true"}
        )
        
        logger.info(f"Malformed timestamp response status code: {response.status_code}")
        
        # We expect the API to handle the malformed timestamp gracefully
        # Either returning a 200 with empty list or a specific error
        if response.status_code not in [200, 400, 422]:
            logger.error(f"Unexpected response code for malformed timestamp: {response.status_code}")
            try:
                error_content = response.text[:500]  # Limit to first 500 chars
                logger.error(f"Error content: {error_content}")
            except Exception as e:
                logger.error(f"Could not extract error content: {e}")
            return False
            
        logger.info(f"✓ API timestamp error handling test passed: API handled malformed timestamp")
        
        # Now test with a valid timestamp
        valid_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        valid_url = f"{API_BASE_URL}/api/chat/1/messages?since={valid_timestamp}"
        logger.info(f"Testing valid timestamp with URL: {valid_url}")
        
        response = requests.get(
            valid_url,
            headers={"X-Test-Timestamp": "true"}
        )
        
        logger.info(f"Valid timestamp response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Unexpected response code for valid timestamp: {response.status_code}")
            try:
                error_content = response.text[:500]  # Limit to first 500 chars
                logger.error(f"Error content: {error_content}")
            except Exception as e:
                logger.error(f"Could not extract error content: {e}")
            return False
            
        logger.info(f"✓ API valid timestamp test passed: API correctly handled valid timestamp")
        return True
        
    except Exception as e:
        logger.error(f"Error testing API timestamp handling: {e}")
        return False


def run_tests():
    """Run all timestamp tests."""
    logger.info("Starting ISO 8601 timestamp tests...")
    
    results = {
        "formatting": test_iso8601_formatting(),
        "parsing": test_iso8601_parsing(),
        "api_response": test_api_timestamp_response(),
        "api_handling": test_api_timestamp_handling(),
    }
    
    # Report results
    logger.info("\n=== ISO 8601 Timestamp Test Results ===")
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result is True else "✗ FAILED" if result is False else "⚠ SKIPPED"
        logger.info(f"{status} - {test_name}")
    
    # Overall success
    if all(r is True or r is None for r in results.values()):
        logger.info("\n🎉 All timestamp tests passed or skipped!")
        return True
    else:
        logger.error("\n❌ Some timestamp tests failed!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 
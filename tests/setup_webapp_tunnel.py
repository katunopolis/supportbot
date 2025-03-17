#!/usr/bin/env python
"""
Setup WebApp Tunnel Script

This script sets up a separate ngrok tunnel for the webapp running on port 3000,
and updates the .env file with the correct WEBAPP_PUBLIC_URL.
"""

import os
import sys
import logging
import subprocess
import time
import json
import requests
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_ngrok_tunnels():
    """Get current ngrok tunnels."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        return response.json()["tunnels"]
    except Exception as e:
        logger.error(f"Failed to get ngrok tunnels: {e}")
        return []

def create_webapp_tunnel():
    """Create a new ngrok tunnel for the webapp."""
    logger.info("Setting up ngrok tunnel for webapp on port 3000...")
    
    try:
        # Check if ngrok is already running
        tunnels = get_ngrok_tunnels()
        webapp_tunnel = None
        
        # Look for an existing webapp tunnel
        for tunnel in tunnels:
            if tunnel.get("config", {}).get("addr", "").endswith("3000"):
                webapp_tunnel = tunnel
                break
        
        # If we found an existing webapp tunnel, use it
        if webapp_tunnel:
            logger.info(f"Found existing webapp tunnel: {webapp_tunnel['public_url']}")
            return webapp_tunnel["public_url"]
        
        # Otherwise, start a new ngrok process for port 3000
        logger.info("No existing webapp tunnel found. Starting new tunnel...")
        
        # Start ngrok in a new process
        process = subprocess.Popen(
            ["ngrok", "http", "3000"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ngrok to start up
        time.sleep(2)
        
        # Get the new tunnels
        tunnels = get_ngrok_tunnels()
        for tunnel in tunnels:
            if tunnel.get("config", {}).get("addr", "").endswith("3000"):
                logger.info(f"Created webapp tunnel: {tunnel['public_url']}")
                return tunnel["public_url"]
        
        logger.error("Failed to create webapp tunnel")
        return None
    except Exception as e:
        logger.error(f"Error creating webapp tunnel: {e}")
        return None

def update_env_file(webapp_url):
    """Update the .env file with the webapp URL."""
    try:
        # Get the path to the .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        
        # Load existing variables
        load_dotenv(env_path)
        
        # Update WEBAPP_PUBLIC_URL
        with open(env_path, "r") as f:
            env_content = f.read()
        
        # Check if WEBAPP_PUBLIC_URL is already in the file
        if "WEBAPP_PUBLIC_URL" in env_content:
            # Update existing value
            lines = env_content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("WEBAPP_PUBLIC_URL="):
                    lines[i] = f"WEBAPP_PUBLIC_URL={webapp_url}"
                    break
            
            # Write updated content
            with open(env_path, "w") as f:
                f.write("\n".join(lines))
        else:
            # Add new value
            with open(env_path, "a") as f:
                f.write(f"\n# WebApp public URL for Telegram WebApp\nWEBAPP_PUBLIC_URL={webapp_url}\n")
        
        logger.info(f"Updated .env file with WEBAPP_PUBLIC_URL={webapp_url}")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False

def main():
    """Main function to set up the webapp tunnel."""
    logger.info("Starting WebApp tunnel setup...")
    
    # Create webapp tunnel
    webapp_url = create_webapp_tunnel()
    if not webapp_url:
        logger.error("Failed to create webapp tunnel")
        return 1
    
    # Update .env file
    if not update_env_file(webapp_url):
        logger.error("Failed to update .env file")
        return 1
    
    logger.info(f"WebApp tunnel setup complete: {webapp_url}")
    logger.info("Restart the bot container to apply changes: docker restart support-bot-supportbot-1")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
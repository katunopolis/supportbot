#!/usr/bin/env python
"""
Support Bot Setup Script

This script automates the setup process for the Support Bot project on a new machine.
It checks for required dependencies, sets up environment variables, and initializes
the project for local development.

Usage:
    python setup.py
"""

import os
import sys
import platform
import subprocess
import shutil
import re
import json
from pathlib import Path

# Configure logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Determine OS
WINDOWS = platform.system() == "Windows"
MACOS = platform.system() == "Darwin"
LINUX = platform.system() == "Linux"

# Constants
DOCKER_COMPOSE_URL = "https://docs.docker.com/compose/install/"
NGROK_URL = "https://ngrok.com/download"
TELEGRAM_API_URL = "https://core.telegram.org/bots#how-do-i-create-a-bot"

class SetupManager:
    """Manages the setup process for the Support Bot project."""

    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.env_file_path = os.path.join(self.project_root, '.env')
        self.docker_compose_path = os.path.join(self.project_root, 'docker-compose.yml')
        self.config = {
            'bot_token': '',
            'admin_group_id': '-4771220922',  # Default admin group ID
            'environment': 'development',
            'ngrok_domain': '',
        }

    def run(self):
        """Run the setup process."""
        print("\n=== Support Bot Setup ===\n")
        
        try:
            self.check_dependencies()
            self.configure_environment()
            self.setup_database()
            self.setup_docker()
            self.finalize_setup()
        except KeyboardInterrupt:
            print("\nSetup interrupted by user. You can run the script again to continue setup.")
            return 1
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            print("\nSetup failed. Please check the error message above.")
            return 1
            
        return 0

    def check_dependencies(self):
        """Check if required dependencies are installed."""
        print("Checking dependencies...\n")
        
        # Check Docker
        if not self._check_command('docker --version'):
            print("Docker is not installed or not in PATH.")
            print(f"Please install Docker from: https://www.docker.com/get-started")
            if not self._confirm("Continue setup without Docker?"):
                raise Exception("Docker is required for this project.")
        else:
            logger.info("✅ Docker is installed")
            
        # Check Docker Compose
        if not self._check_command('docker-compose --version') and not self._check_command('docker compose version'):
            print("Docker Compose is not installed or not in PATH.")
            print(f"Please install Docker Compose from: {DOCKER_COMPOSE_URL}")
            if not self._confirm("Continue setup without Docker Compose?"):
                raise Exception("Docker Compose is required for this project.")
        else:
            logger.info("✅ Docker Compose is installed")
            
        # Check ngrok
        if not self._check_command('ngrok --version'):
            print("ngrok is not installed or not in PATH.")
            print(f"Please install ngrok from: {NGROK_URL}")
            print("After installation, you'll need to authenticate with: ngrok authtoken YOUR_AUTH_TOKEN")
            if not self._confirm("Continue setup without ngrok?"):
                raise Exception("ngrok is required for local development.")
        else:
            logger.info("✅ ngrok is installed")
            
        # Check Python version
        python_version = platform.python_version()
        if not self._version_check(python_version, '3.9.0'):
            print(f"Warning: Your Python version ({python_version}) is older than the recommended version (3.9+)")
            if not self._confirm("Continue with the current Python version?"):
                raise Exception("Python 3.9+ is recommended for this project.")
        else:
            logger.info(f"✅ Python {python_version} is installed")
            
        print("\nDependency check completed.\n")

    def configure_environment(self):
        """Configure environment variables."""
        print("Configuring environment variables...\n")
        
        # Check if .env file already exists
        if os.path.exists(self.env_file_path):
            if self._confirm(".env file already exists. Do you want to overwrite it?"):
                os.remove(self.env_file_path)
            else:
                print("Keeping existing .env file.")
                # Load existing values
                self._load_env_file()
                return
        
        # Bot token
        if not self.config['bot_token']:
            print("\nPlease enter your Telegram Bot Token from @BotFather")
            print(f"If you don't have one, create it at: {TELEGRAM_API_URL}")
            self.config['bot_token'] = input("Bot Token: ").strip()
            
            if not self.config['bot_token']:
                print("Bot token is required. Using a placeholder for now.")
                self.config['bot_token'] = "YOUR_BOT_TOKEN_HERE"
        
        # Admin group ID
        print("\nPlease enter your Telegram Admin Group ID")
        print("This is the group where admin notifications will be sent")
        print(f"Current value: {self.config['admin_group_id']}")
        admin_group_id = input("Admin Group ID (press Enter to keep current): ").strip()
        if admin_group_id:
            self.config['admin_group_id'] = admin_group_id
            
        # Create .env file
        self._create_env_file()
        print("\nEnvironment configuration completed.\n")

    def setup_database(self):
        """Set up the database configuration."""
        print("Setting up database configuration...\n")
        
        # Database is handled by Docker Compose, so we just need to check if it's configured properly
        if os.path.exists(self.docker_compose_path):
            print("Database will be set up via Docker Compose.")
            print("The default configuration uses PostgreSQL with the following settings:")
            print("  - Host: db")
            print("  - Port: 5432")
            print("  - Username: postgres")
            print("  - Password: postgres")
            print("  - Database: supportbot")
            print("\nThese settings are configured in docker-compose.yml and .env file.")
        else:
            print("Warning: docker-compose.yml not found. Database setup may be incomplete.")
            
        print("\nDatabase configuration completed.\n")

    def setup_docker(self):
        """Set up Docker containers."""
        if self._check_command('docker --version') and (self._check_command('docker-compose --version') or self._check_command('docker compose version')):
            print("Docker and Docker Compose are available.")
            if self._confirm("Do you want to build Docker containers now?"):
                print("Building Docker containers (this may take a few minutes)...")
                
                result = subprocess.run(
                    ['docker-compose', 'build'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("✅ Docker containers built successfully")
                    print("Docker containers built successfully.")
                else:
                    logger.error(f"Failed to build Docker containers: {result.stderr}")
                    print(f"Failed to build Docker containers. Error: {result.stderr}")
        else:
            print("Skipping Docker setup as Docker or Docker Compose is not installed.")

    def finalize_setup(self):
        """Finalize the setup process."""
        print("\n=== Setup Complete ===\n")
        
        print("Your Support Bot project has been configured successfully!")
        print("\nTo start the application:")
        print("1. Start Docker containers:")
        print("   docker-compose up -d")
        print("\n2. Start ngrok for local development:")
        print("   ngrok http 8000")
        print("\n3. Update ngrok URL in configuration:")
        print("   python fresh-setup/ngrok_update.py")
        print("\n4. Test bot connection:")
        print("   python run_test.py bot")
        print("\nFor more information, check the documentation in the docs/ folder.")
        
        # Create a setup completion file
        with open(os.path.join(self.project_root, '.setup_complete'), 'w') as f:
            f.write(f"Setup completed on: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, None, None, None))}\n")
            f.write(f"Python version: {platform.python_version()}\n")
            f.write(f"OS: {platform.system()} {platform.release()}\n")
        
        print("\nSetup information saved. You're all set to go!\n")

    def _check_command(self, command):
        """Check if a command is available in the system."""
        try:
            subprocess.run(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _version_check(self, current, minimum):
        """Check if the current version meets the minimum requirement."""
        current_parts = list(map(int, current.split('.')))
        minimum_parts = list(map(int, minimum.split('.')))
        
        for i in range(max(len(current_parts), len(minimum_parts))):
            current_part = current_parts[i] if i < len(current_parts) else 0
            minimum_part = minimum_parts[i] if i < len(minimum_parts) else 0
            
            if current_part > minimum_part:
                return True
            elif current_part < minimum_part:
                return False
                
        return True  # Equal versions

    def _confirm(self, question):
        """Ask for user confirmation."""
        while True:
            response = input(f"{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'.")

    def _create_env_file(self):
        """Create the .env file with the configured values."""
        env_template = f"""# Bot configuration
SUPPORT_BOT_TOKEN={self.config['bot_token']}

# Database configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/supportbot

# Connection pool settings
MAX_CONNECTIONS=20
POOL_TIMEOUT=30

# Environment (development/production)
ENVIRONMENT={self.config['environment']}

# Railway settings (needed even for local development)
# For local testing with ngrok, use your ngrok URL without https:// prefix
# Example: 1a2b3c4d.ngrok.io
RAILWAY_PUBLIC_DOMAIN=your-ngrok-domain-here.ngrok-free.app

# Admin group ID for notifications
ADMIN_GROUP_ID={self.config['admin_group_id']}

# WebApp URLs (needed for Telegram WebApp functionality)
BASE_WEBAPP_URL=https://your-ngrok-domain-here.ngrok-free.app
WEB_APP_URL=https://your-ngrok-domain-here.ngrok-free.app/support-form.html
"""
        
        with open(self.env_file_path, 'w') as f:
            f.write(env_template)
            
        logger.info(f"✅ Created .env file at {self.env_file_path}")
        
    def _load_env_file(self):
        """Load values from existing .env file."""
        try:
            with open(self.env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key == 'SUPPORT_BOT_TOKEN':
                            self.config['bot_token'] = value
                        elif key == 'ADMIN_GROUP_ID':
                            self.config['admin_group_id'] = value
                        elif key == 'ENVIRONMENT':
                            self.config['environment'] = value
                        elif key == 'RAILWAY_PUBLIC_DOMAIN':
                            self.config['ngrok_domain'] = value
                            
            logger.info(f"✅ Loaded configuration from existing .env file")
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")

if __name__ == "__main__":
    setup = SetupManager()
    sys.exit(setup.run()) 
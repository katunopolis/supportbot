#!/usr/bin/env python
"""
Ngrok Installer Utility

This script automatically downloads and installs ngrok on Windows, macOS, or Linux.
It handles:
1. Downloading the appropriate ngrok version for your OS
2. Extracting it to a suitable location
3. Adding it to your PATH
4. Setting up authentication
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile
import logging
import zipfile
import tarfile
import urllib.request
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Determine OS
WINDOWS = platform.system() == "Windows"
MACOS = platform.system() == "Darwin"
LINUX = platform.system() == "Linux"

# Determine architecture
ARCH_64 = platform.machine().endswith('64')
ARM = platform.machine().startswith('arm') or platform.machine().startswith('aarch')

class NgrokInstaller:
    """Handles the installation of ngrok."""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.download_url = self._get_download_url()
        self.install_dir = self._get_install_dir()
        self.ngrok_path = os.path.join(self.install_dir, "ngrok.exe" if WINDOWS else "ngrok")
        
    def _get_download_url(self):
        """Get the appropriate download URL for the current OS and architecture."""
        base_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-"
        
        if WINDOWS:
            return f"{base_url}{'windows-arm64.zip' if ARM else 'windows-amd64.zip'}"
        elif MACOS:
            return f"{base_url}{'darwin-arm64.zip' if ARM else 'darwin-amd64.zip'}"
        elif LINUX:
            return f"{base_url}{'linux-arm64.tgz' if ARM else 'linux-amd64.tgz'}"
        else:
            raise Exception(f"Unsupported operating system: {platform.system()}")
    
    def _get_install_dir(self):
        """Get the installation directory for ngrok."""
        if WINDOWS:
            return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local')), 'ngrok')
        else:
            return os.path.join(os.path.expanduser('~'), '.ngrok2')
            
    def download(self):
        """Download ngrok from the official website."""
        print(f"Downloading ngrok from {self.download_url}")
        
        download_path = os.path.join(self.temp_dir, "ngrok.zip" if WINDOWS or MACOS else "ngrok.tgz")
        
        try:
            urllib.request.urlretrieve(self.download_url, download_path)
            logger.info(f"✅ Downloaded ngrok to {download_path}")
            return download_path
        except Exception as e:
            logger.error(f"Failed to download ngrok: {str(e)}")
            raise
    
    def extract(self, download_path):
        """Extract the downloaded ngrok archive."""
        print(f"Extracting ngrok to {self.install_dir}")
        
        # Create installation directory if it doesn't exist
        os.makedirs(self.install_dir, exist_ok=True)
        
        try:
            if download_path.endswith('.zip'):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(self.install_dir)
            else:  # .tgz or .tar.gz
                with tarfile.open(download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.install_dir)
                    
            logger.info(f"✅ Extracted ngrok to {self.install_dir}")
        except Exception as e:
            logger.error(f"Failed to extract ngrok: {str(e)}")
            raise
    
    def add_to_path(self):
        """Add ngrok to the PATH."""
        print("Adding ngrok to PATH")
        
        if WINDOWS:
            # Check if already in PATH
            paths = os.environ.get('PATH', '').split(os.pathsep)
            if self.install_dir.lower() in [p.lower() for p in paths]:
                logger.info("✅ ngrok is already in PATH")
                return
                
            try:
                # Add to user PATH using setx
                result = subprocess.run(
                    ['setx', 'PATH', f"{os.environ.get('PATH', '')}{os.pathsep}{self.install_dir}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    logger.info("✅ Added ngrok to PATH")
                    print("NOTE: You'll need to restart your terminal for the PATH change to take effect.")
                else:
                    logger.error(f"Failed to add ngrok to PATH: {result.stderr}")
                    raise Exception(f"Failed to add ngrok to PATH: {result.stderr}")
            except Exception as e:
                logger.error(f"Error adding ngrok to PATH: {str(e)}")
                print(f"To manually add ngrok to PATH, add: {self.install_dir}")
        else:
            # For macOS and Linux, suggest adding to .bashrc or .zshrc
            shell_file = os.path.expanduser("~/.zshrc" if os.path.exists(os.path.expanduser("~/.zshrc")) else "~/.bashrc")
            print(f"To add ngrok to PATH, add this line to {shell_file}:")
            print(f'export PATH="$PATH:{self.install_dir}"')
            
    def setup_auth(self):
        """Set up ngrok authentication."""
        print("\nTo complete the ngrok setup, you need to authenticate with your authtoken.")
        print("You can get your authtoken by signing up at https://ngrok.com/signup")
        print("After signing up, find your authtoken at: https://dashboard.ngrok.com/get-started/your-authtoken")
        
        authtoken = input("\nEnter your ngrok authtoken (press Enter to skip for now): ").strip()
        
        if authtoken:
            try:
                # Run ngrok authtoken command
                result = subprocess.run(
                    [self.ngrok_path, "authtoken", authtoken],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    logger.info("✅ Authenticated ngrok successfully")
                    print("ngrok authentication successful!")
                else:
                    logger.error(f"Failed to authenticate ngrok: {result.stderr}")
                    print(f"Failed to authenticate ngrok. Error: {result.stderr}")
            except Exception as e:
                logger.error(f"Error authenticating ngrok: {str(e)}")
                print(f"Error authenticating ngrok: {str(e)}")
        else:
            print("\nYou skipped authentication. Remember to run this command later:")
            print(f"  {self.ngrok_path} authtoken YOUR_AUTH_TOKEN")
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"✅ Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to clean up temporary directory: {str(e)}")
    
    def install(self):
        """Run the full installation process."""
        try:
            download_path = self.download()
            self.extract(download_path)
            self.add_to_path()
            self.setup_auth()
            self.cleanup()
            
            print("\n=== ngrok Installation Complete ===")
            print(f"ngrok executable location: {self.ngrok_path}")
            print("\nTo start a tunnel for your Telegram bot:")
            print(f"  {self.ngrok_path} http 8000")
            print("\nAfter starting ngrok, update your bot's webhook URL using:")
            print("  python fresh-setup/ngrok_update.py")
            
            return True
        except Exception as e:
            logger.error(f"Installation failed: {str(e)}")
            print(f"\nInstallation failed: {str(e)}")
            return False

def main():
    """Main function to run the installer."""
    print("=== ngrok Installer ===\n")
    print("This utility will download and install ngrok on your system.")
    
    installer = NgrokInstaller()
    success = installer.install()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
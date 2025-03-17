#!/usr/bin/env python
"""
Ngrok Troubleshooting Utility

This script helps troubleshoot common ngrok issues, such as:
1. Finding ngrok if it's installed but not in PATH
2. Checking firewall settings that might block ngrok
3. Verifying ngrok authentication
4. Providing instructions for proper ngrok setup
"""

import os
import sys
import platform
import subprocess
import shutil
import logging

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

def check_ngrok_installation():
    """Check if ngrok is installed and available."""
    print("Checking ngrok installation...")
    
    # Check if ngrok is in PATH
    ngrok_in_path = shutil.which("ngrok") is not None
    if ngrok_in_path:
        print("✅ ngrok is in your PATH")
        try:
            result = subprocess.run(
                ["ngrok", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print(f"✅ ngrok version: {result.stdout.strip()}")
            else:
                print("❌ ngrok is in PATH but failed to run")
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ Error running ngrok: {str(e)}")
    else:
        print("❌ ngrok is not in your PATH")
        
        # Look for ngrok in common installation locations
        possible_locations = []
        if WINDOWS:
            possible_locations = [
                r"C:\ProgramData\chocolatey\bin\ngrok.exe",
                r"C:\ProgramData\chocolatey\lib\ngrok\tools\ngrok.exe",
                os.path.expanduser("~/AppData/Local/ngrok/ngrok.exe"),
                os.path.expanduser("~/ngrok.exe"),
            ]
        elif MACOS:
            possible_locations = [
                "/usr/local/bin/ngrok",
                "/opt/homebrew/bin/ngrok",
                os.path.expanduser("~/ngrok"),
            ]
        elif LINUX:
            possible_locations = [
                "/usr/bin/ngrok",
                "/usr/local/bin/ngrok",
                os.path.expanduser("~/ngrok"),
            ]
            
        for location in possible_locations:
            if os.path.exists(location):
                print(f"✅ Found ngrok at: {location}")
                print(f"   To add to PATH, try: {get_path_command(location)}")
                return location
                
        print("❌ ngrok not found in common locations")
        print("Please download ngrok from: https://ngrok.com/download")
        
    return ngrok_in_path

def check_ngrok_auth():
    """Check ngrok authentication status."""
    print("\nChecking ngrok authentication...")
    
    ngrok_config_file = None
    if WINDOWS:
        ngrok_config_file = os.path.expanduser(r"~\AppData\Local\ngrok\ngrok.yml")
    elif MACOS or LINUX:
        ngrok_config_file = os.path.expanduser("~/.ngrok2/ngrok.yml")
        
    if ngrok_config_file and os.path.exists(ngrok_config_file):
        print(f"✅ Found ngrok config file: {ngrok_config_file}")
        
        # Check if the file contains an authtoken
        try:
            with open(ngrok_config_file, 'r') as f:
                content = f.read()
                if "authtoken:" in content:
                    print("✅ ngrok authtoken is set")
                else:
                    print("❌ ngrok authtoken is not set in config file")
                    print("Run: ngrok authtoken YOUR_AUTH_TOKEN")
        except Exception as e:
            print(f"❌ Error reading ngrok config file: {str(e)}")
    else:
        print(f"❌ ngrok config file not found at {ngrok_config_file}")
        print("Run: ngrok authtoken YOUR_AUTH_TOKEN")

def check_firewall():
    """Check firewall settings that might block ngrok."""
    print("\nChecking firewall and connectivity...")
    
    # Try to connect to ngrok.com
    print("Testing connection to ngrok.com...")
    try:
        result = subprocess.run(
            ["ping", "ngrok.com", "-c", "3"] if not WINDOWS else ["ping", "ngrok.com", "-n", "3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("✅ Connection to ngrok.com successful")
        else:
            print("❌ Connection to ngrok.com failed")
            print("This might indicate a network or firewall issue")
            print("Please check your firewall settings to allow outbound connections to ngrok.com")
            
    except Exception as e:
        print(f"❌ Error testing connection: {str(e)}")
    
    # Check for specific ports
    print("\nChecking outbound connectivity to required ports...")
    ports_to_check = [443, 4443]
    
    for port in ports_to_check:
        if WINDOWS:
            # On Windows, use PowerShell to test connection
            cmd = ["powershell", "-Command", f"Test-NetConnection -ComputerName ngrok.com -Port {port}"]
        else:
            # On Unix systems, use nc (netcat)
            timeout_cmd = "timeout" if LINUX else "gtimeout" if MACOS else "timeout"
            cmd = [timeout_cmd, "5", "nc", "-z", "ngrok.com", str(port)]
            
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"✅ Port {port} is accessible")
            else:
                print(f"❌ Port {port} is blocked. This will prevent ngrok from working properly.")
                
        except Exception as e:
            print(f"❌ Error checking port {port}: {str(e)}")
    
    if WINDOWS:
        print("\nOn Windows, Bitdefender and other antivirus software may block ngrok.")
        print("Consider temporarily disabling the firewall or adding an exception for ngrok.exe")

def test_ngrok():
    """Test ngrok by starting a simple tunnel."""
    print("\nTesting ngrok tunnel...")
    
    # Try to start ngrok
    try:
        # Use subprocess.Popen to start ngrok in the background
        print("Starting ngrok on port 80 (will be terminated after a few seconds)...")
        if WINDOWS:
            # On Windows, we need to use a different approach to prevent console window
            process = subprocess.Popen(
                ["ngrok", "http", "80"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            process = subprocess.Popen(
                ["ngrok", "http", "80"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
        # Wait a few seconds for ngrok to start
        import time
        time.sleep(5)
        
        # Check if ngrok API is available
        api_result = subprocess.run(
            ["curl", "-s", "http://localhost:4040/api/tunnels"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if "tunnel_name" in api_result.stdout or "url" in api_result.stdout:
            print("✅ ngrok tunnel started successfully")
            print("Your ngrok installation appears to be working correctly")
        else:
            print("❌ ngrok tunnel failed to start properly")
            print("API response:", api_result.stdout)
            
        # Terminate ngrok
        process.terminate()
        
    except Exception as e:
        print(f"❌ Error testing ngrok: {str(e)}")
        print("This might be due to permission issues or ngrok already running")

def get_path_command(ngrok_path):
    """Get the command to add ngrok to PATH."""
    if WINDOWS:
        return f'setx PATH "%PATH%;{os.path.dirname(ngrok_path)}"'
    elif MACOS or LINUX:
        return f'export PATH="$PATH:{os.path.dirname(ngrok_path)}" && echo \'export PATH="$PATH:{os.path.dirname(ngrok_path)}"\' >> ~/.bashrc'

def provide_instructions():
    """Provide instructions for fixing common ngrok issues."""
    print("\n=== Fixing Common ngrok Issues ===")
    
    print("\n1. Installing ngrok:")
    print("   - Download from: https://ngrok.com/download")
    print("   - Extract the executable to a folder in your PATH")
    print("   - Set up authentication: ngrok authtoken YOUR_AUTH_TOKEN")
    
    print("\n2. Firewall/Antivirus Issues:")
    print("   - Temporarily disable firewall/antivirus to test if it's blocking ngrok")
    print("   - Add ngrok.exe as an exception in your firewall/antivirus")
    print("   - Ensure outbound connections to *.ngrok.com are allowed")
    print("   - Required ports: 443, 4443")
    
    print("\n3. Connection Issues:")
    print("   - Try using a VPN to bypass ISP restrictions")
    print("   - Check if your network blocks outbound connections")
    print("   - Verify that you're using the latest version of ngrok")
    
    print("\n4. Finding and using ngrok:")
    print("   - If ngrok is installed but not in PATH, use the full path to run it")
    print("   - On Windows: C:\\path\\to\\ngrok.exe http 8000")
    print("   - On macOS/Linux: /path/to/ngrok http 8000")
    
    print("\n5. Getting help:")
    print("   - ngrok documentation: https://ngrok.com/docs")
    print("   - ngrok status page: https://status.ngrok.com")

def main():
    """Main function to run the script."""
    print("=== Ngrok Troubleshooting Utility ===\n")
    
    check_ngrok_installation()
    check_ngrok_auth()
    check_firewall()
    
    if shutil.which("ngrok") is not None:
        if input("\nDo you want to test ngrok by starting a tunnel? (y/n): ").lower().strip() in ['y', 'yes']:
            test_ngrok()
    
    provide_instructions()
    
    print("\n=== Troubleshooting Complete ===")
    print("If you're still having issues, please check the documentation at https://ngrok.com/docs")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
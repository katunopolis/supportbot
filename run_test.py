#!/usr/bin/env python
"""
Test runner script for Support Bot

This script provides a simple way to run tests from the project root.
"""

import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Run Support Bot tests')
    
    # Create a choices dictionary with descriptions for each test
    test_choices = {
        'bot': 'Test the bot connection to the Telegram API',
        'webhook-set': 'Set up the webhook using test_webhook_setup.py',
        'webhook-delete': 'Delete the existing webhook',
        'webapp': 'Test the webapp URLs',
        'local': 'Test the local webapp',
        'webapp-tunnel': 'Set up a tunnel for the webapp',
        'ngrok-update': 'Update ngrok URLs in configuration using ngrok_link_update.py',
        'container-webhook': 'Update the webhook inside the container using update_webhook_in_container.py',
        'webhook-update': 'Update webhook URL with interactive prompt or command line argument',
        'timestamps': 'Test ISO 8601 timestamp handling functionality'
    }
    
    # Create the argument parser with choices and help
    parser.add_argument(
        'test_type',
        choices=list(test_choices.keys()),
        help='Type of test to run'
    )
    
    # Add an optional URL parameter for webhook-update
    parser.add_argument(
        '--url',
        help='The ngrok URL to use with webhook-update (e.g., https://xxxx-xx-xx-xx-xx.ngrok-free.app)'
    )
    
    # Add a description of each choice to the help text
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.epilog = "Available test types:\n" + "\n".join(
        [f"  {key}: {value}" for key, value in test_choices.items()]
    )
    
    args = parser.parse_args()
    
    # Change to the tests directory
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))
    
    # Run the appropriate test
    if args.test_type == 'bot':
        subprocess.run([sys.executable, 'test_bot_connection.py'])
    elif args.test_type == 'webhook-set':
        subprocess.run([sys.executable, 'test_webhook_setup.py', '--action', 'set'])
    elif args.test_type == 'webhook-delete':
        subprocess.run([sys.executable, 'test_webhook_setup.py', '--action', 'delete'])
    elif args.test_type == 'webapp':
        subprocess.run([sys.executable, 'test_webapp_url.py'])
    elif args.test_type == 'local':
        subprocess.run([sys.executable, 'test_local_webapp.py'])
    elif args.test_type == 'webapp-tunnel':
        subprocess.run([sys.executable, 'setup_webapp_tunnel.py'])
    elif args.test_type == 'ngrok-update':
        subprocess.run([sys.executable, 'ngrok_link_update.py'])
    elif args.test_type == 'container-webhook':
        subprocess.run([sys.executable, 'update_webhook_in_container.py'])
    elif args.test_type == 'webhook-update':
        cmd = [sys.executable, 'test_webhook.py']
        if args.url:
            cmd.extend(['--url', args.url])
        subprocess.run(cmd)
    elif args.test_type == 'timestamps':
        subprocess.run([sys.executable, 'test_timestamp_handling.py'])
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 
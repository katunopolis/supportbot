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
    parser.add_argument('test_type', choices=['bot', 'webhook-set', 'webhook-delete', 'webapp', 'local', 'webapp-tunnel'],
                        help='Type of test to run')
    
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
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 
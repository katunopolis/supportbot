#!/usr/bin/env python
"""
Support Bot Log Monitor

This utility provides a real-time view of the logs from different services,
making it easier to debug issues as they happen.
"""

import os
import sys
import subprocess
import threading
import time
import argparse
from datetime import datetime
import re

# ANSI color codes for colorizing output
COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
}

# Service configuration
SERVICES = {
    'bot': {
        'container': 'support-bot-supportbot-1',
        'color': 'green',
        'patterns': {
            'error': r'ERROR|Exception|stack trace',
            'warning': r'WARNING|WARN',
            'info': r'INFO',
            'debug': r'DEBUG',
            'telegram': r'telegram|bot|webhook',
        }
    },
    'webapp': {
        'container': 'support-bot-webapp-1',
        'color': 'blue',
        'patterns': {
            'error': r'ERROR|Exception|stack trace',
            'warning': r'WARNING|WARN',
            'info': r'INFO',
            'debug': r'DEBUG',
            'request': r'GET|POST|PUT|DELETE',
        }
    },
    'db': {
        'container': 'support-bot-db-1',
        'color': 'yellow',
        'patterns': {
            'error': r'ERROR|FATAL|PANIC',
            'warning': r'WARNING|WARN',
            'info': r'LOG|INFO',
            'transaction': r'TRANSACTION',
        }
    }
}

def colorize(text, color):
    """Add color to text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def timestamp():
    """Get current timestamp for logging."""
    return datetime.now().strftime('%H:%M:%S')

def stream_logs(service_name, options):
    """Stream logs from a specific service."""
    service = SERVICES[service_name]
    container = service['color']
    color = service['color']
    
    # Build the docker logs command
    follow_flag = "-f" if options.follow else ""
    tail_flag = f"--tail {options.lines}"
    
    cmd = f"docker logs {follow_flag} {tail_flag} {service['container']}"
    
    # Print startup message
    header = f" Monitoring {service_name.upper()} logs "
    print(colorize(f"\n{'-'*10}{header}{'-'*10}", color))
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Process each line
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue
                
            # Apply highlighting for patterns
            highlighted = line
            for pattern_type, pattern in service['patterns'].items():
                if re.search(pattern, line, re.IGNORECASE):
                    if pattern_type == 'error':
                        highlighted = colorize(line, 'red')
                    elif pattern_type == 'warning':
                        highlighted = colorize(line, 'yellow')
                    else:
                        highlighted = colorize(line, color)
                    break
                    
            # Print with service prefix
            prefix = colorize(f"[{timestamp()} {service_name.upper()}]", color)
            print(f"{prefix} {highlighted}")
            
        process.wait()
    except KeyboardInterrupt:
        if process:
            process.terminate()
        print(colorize(f"\n[{timestamp()}] Stopped monitoring {service_name} logs", color))
    except Exception as e:
        print(colorize(f"\n[{timestamp()}] Error monitoring {service_name} logs: {e}", 'red'))

def monitor_all(options):
    """Monitor logs from all services concurrently."""
    threads = []
    
    try:
        # Start a thread for each service
        for service_name in options.services:
            if service_name not in SERVICES:
                print(colorize(f"Unknown service: {service_name}", 'red'))
                continue
                
            thread = threading.Thread(
                target=stream_logs,
                args=(service_name, options),
                daemon=True
            )
            threads.append(thread)
            thread.start()
            
        # Wait for all threads to complete (or until KeyboardInterrupt)
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print(colorize("\n[{}] Log monitoring stopped".format(timestamp()), 'white'))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Monitor Support Bot logs")
    parser.add_argument(
        "-s", "--services",
        nargs="+",
        choices=list(SERVICES.keys()) + ["all"],
        default=["bot"],
        help="Services to monitor (bot, webapp, db, or all)"
    )
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow logs in real-time"
    )
    parser.add_argument(
        "-l", "--lines",
        type=int,
        default=50,
        help="Number of log lines to show"
    )
    parser.add_argument(
        "-e", "--errors-only",
        action="store_true",
        help="Show only errors and warnings"
    )
    
    args = parser.parse_args()
    
    # Handle 'all' option
    if "all" in args.services:
        args.services = list(SERVICES.keys())
        
    return args

def main():
    """Main function to run the log monitor."""
    print(colorize("=== Support Bot Log Monitor ===", 'bold'))
    print("Press Ctrl+C to stop monitoring\n")
    
    options = parse_arguments()
    monitor_all(options)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
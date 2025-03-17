# Fresh Setup Utilities

This folder contains utility scripts for setting up the Support Bot on a new machine or updating its configuration.

## Available Scripts

### `setup.py`

The main setup script for configuring the Support Bot on a new machine. It:

- Checks for required dependencies (Docker, Docker Compose, ngrok, Python)
- Configures environment variables
- Sets up database configuration
- Builds Docker containers
- Provides next steps for starting the application

**Usage:**
```bash
python fresh-setup/setup.py
```

### `ngrok_installer.py`

A dedicated installer for ngrok that handles downloading, installing, and configuring ngrok on Windows, macOS, or Linux. It:

- Downloads the appropriate ngrok version for your OS and architecture
- Extracts it to a suitable location
- Adds it to your PATH
- Sets up authentication with your ngrok authtoken

**Usage:**
```bash
python fresh-setup/ngrok_installer.py
```

### `ngrok_update.py`

A utility for updating the ngrok URL when it changes. This is especially useful for local development since free ngrok URLs change each time you restart ngrok.

The script:
- Updates the `.env` file with the new ngrok URL
- Restarts the supportbot container
- Sets the webhook with the new URL
- Tests the bot connection

**Usage:**
```bash
python fresh-setup/ngrok_update.py
```

### `fix_ngrok.py`

A utility for troubleshooting common ngrok issues. It:

- Checks if ngrok is installed and in PATH
- Looks for ngrok in common installation locations
- Verifies ngrok authentication status
- Tests firewall settings and connectivity
- Provides detailed instructions for fixing common issues

**Usage:**
```bash
python fresh-setup/fix_ngrok.py
```

### `monitor_logs.py`

A colorized log monitoring utility for real-time debugging. It:

- Displays logs from multiple services (bot, webapp, db) in different colors
- Highlights errors, warnings, and important information
- Supports filtering by service or log level
- Provides real-time log streaming

**Usage:**
```bash
python fresh-setup/monitor_logs.py --services bot webapp db --follow
```

**Options:**
- `-s, --services`: Services to monitor (bot, webapp, db, or all)
- `-f, --follow`: Follow logs in real-time
- `-l, --lines`: Number of log lines to show (default: 50)
- `-e, --errors-only`: Show only errors and warnings

## Common Use Cases

### Setting up on a new machine

1. Clone the repository
2. Run the setup script:
   ```bash
   python fresh-setup/setup.py
   ```
3. Follow the prompts to configure your bot

### Installing ngrok

If you encounter issues with ngrok, use the dedicated installer:

1. Run the ngrok installer:
   ```bash
   python fresh-setup/ngrok_installer.py
   ```
2. Follow the prompts to install and configure ngrok

### Updating ngrok URL

1. Start ngrok:
   ```bash
   ngrok http 8000
   ```
2. Copy the HTTPS URL from the ngrok output
3. Run the ngrok update script:
   ```bash
   python fresh-setup/ngrok_update.py
   ```
4. Enter the ngrok URL when prompted

### Monitoring logs for debugging

1. To monitor all services in real-time:
   ```bash
   python fresh-setup/monitor_logs.py --services all --follow
   ```

2. To only see errors and warnings:
   ```bash
   python fresh-setup/monitor_logs.py --services all --follow --errors-only
   ```

## Documentation

For detailed setup instructions, see [docs/SETUP.md](../docs/SETUP.md) 
#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update the .env file with your actual configuration values."
    exit 1
fi

# Handle command line arguments
command=${1:-help}

case $command in
    up)
        echo "Starting local development environment..."
        docker compose up --build
        ;;
    down)
        echo "Stopping local development environment..."
        docker compose down
        ;;
    restart)
        echo "Restarting local development environment..."
        docker compose restart
        ;;
    logs)
        echo "Showing logs..."
        docker compose logs -f
        ;;
    shell)
        echo "Opening shell in the container..."
        docker compose exec supportbot bash
        ;;
    test)
        echo "Running tests..."
        docker compose exec supportbot pytest
        ;;
    help)
        echo "Support Bot Development Helper"
        echo "---------------------------"
        echo "Commands:"
        echo "  up       - Start local development environment"
        echo "  down     - Stop local development environment"
        echo "  restart  - Restart services"
        echo "  logs     - Show logs"
        echo "  shell    - Open shell in the container"
        echo "  test     - Run tests"
        ;;
    *)
        echo "Unknown command: $command"
        echo "Run './dev.sh help' for available commands"
        ;;
esac 
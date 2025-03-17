# Parse command line arguments
param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..."
    Copy-Item .env.example .env
    Write-Host "Please update the .env file with your actual configuration values."
    exit
}

switch ($Command) {
    "up" {
        Write-Host "Starting local development environment..."
        docker compose up --build
    }
    "down" {
        Write-Host "Stopping local development environment..."
        docker compose down
    }
    "restart" {
        Write-Host "Restarting local development environment..."
        docker compose restart
    }
    "logs" {
        Write-Host "Showing logs..."
        docker compose logs -f
    }
    "shell-api" {
        Write-Host "Opening shell in the supportbot container..."
        docker compose exec supportbot bash
    }
    "shell-web" {
        Write-Host "Opening shell in the webapp container..."
        docker compose exec webapp sh
    }
    "test" {
        Write-Host "Running tests..."
        docker compose exec supportbot pytest
    }
    "help" {
        Write-Host "Support Bot Development Helper"
        Write-Host "---------------------------"
        Write-Host "Commands:"
        Write-Host "  up         - Start local development environment"
        Write-Host "  down       - Stop local development environment"
        Write-Host "  restart    - Restart services"
        Write-Host "  logs       - Show logs"
        Write-Host "  shell-api  - Open shell in the API container"
        Write-Host "  shell-web  - Open shell in the webapp container"
        Write-Host "  test       - Run tests"
    }
    default {
        Write-Host "Unknown command: $Command"
        Write-Host "Run './dev.ps1 help' for available commands"
    }
} 
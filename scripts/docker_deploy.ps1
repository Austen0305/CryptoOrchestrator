# Docker Deployment Automation Script (PowerShell)
# Handles building, tagging, and deploying Docker containers

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "scan", "push", "deploy", "migrate", "health", "rollback")]
    [string]$Action = "build",
    
    [string]$Registry = $env:DOCKER_REGISTRY ?? "ghcr.io",
    [string]$ImageName = $env:DOCKER_IMAGE_NAME ?? "cryptoorchestrator",
    [string]$Version = $env:VERSION ?? (git describe --tags --always),
    [string]$Environment = $env:ENVIRONMENT ?? "staging"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message, [string]$Color = "Green")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Error-Log {
    param([string]$Message)
    Write-Log $Message "Red"
}

function Write-Warning-Log {
    param([string]$Message)
    Write-Log $Message "Yellow"
}

function Write-Info-Log {
    param([string]$Message)
    Write-Log $Message "Cyan"
}

function Build-Image {
    Write-Log "Building Docker image..."
    docker build `
        -t "${ImageName}:${Version}" `
        -t "${ImageName}:latest" `
        -t "${Registry}/${ImageName}:${Version}" `
        -t "${Registry}/${ImageName}:latest" `
        -f Dockerfile `
        .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Docker build failed"
        exit 1
    }
    
    Write-Log "✓ Docker image built successfully"
}

function Security-Scan {
    Write-Log "Running security scan..."
    if (Get-Command trivy -ErrorAction SilentlyContinue) {
        trivy image --exit-code 0 --severity HIGH,CRITICAL "${ImageName}:${Version}"
        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Log "Security scan found issues"
        }
    } else {
        Write-Warning-Log "Trivy not installed, skipping security scan"
    }
}

function Push-Image {
    if (-not $env:DOCKER_USERNAME -or -not $env:DOCKER_PASSWORD) {
        Write-Warning-Log "DOCKER_USERNAME or DOCKER_PASSWORD not set, skipping push"
        return
    }
    
    Write-Log "Logging into Docker registry..."
    $env:DOCKER_PASSWORD | docker login "${Registry}" -u "$env:DOCKER_USERNAME" --password-stdin
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Docker login failed"
        exit 1
    }
    
    Write-Log "Pushing images to registry..."
    docker push "${Registry}/${ImageName}:${Version}"
    docker push "${Registry}/${ImageName}:latest"
    
    Write-Log "✓ Images pushed successfully"
}

function Deploy-Compose {
    Write-Log "Deploying with docker-compose..."
    
    $env:IMAGE_TAG = $Version
    $env:ENV = $Environment
    
    $composeFile = "docker-compose.yml"
    if (Test-Path "docker-compose.${Environment}.yml") {
        $composeFile = "docker-compose.yml", "docker-compose.${Environment}.yml"
    }
    
    docker-compose -f docker-compose.yml pull
    docker-compose -f docker-compose.yml up -d --force-recreate
    
    Write-Log "✓ Deployment completed"
}

function Run-Migrations {
    Write-Log "Running database migrations..."
    docker-compose exec -T backend python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Migrations failed"
        exit 1
    }
    Write-Log "✓ Migrations completed"
}

function Health-Check {
    Write-Log "Performing health check..."
    $maxRetries = 30
    $retryCount = 0
    
    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ Health check passed"
                return
            }
        } catch {
            # Continue retrying
        }
        
        $retryCount++
        Start-Sleep -Seconds 2
    }
    
    Write-Error-Log "Health check failed after $maxRetries attempts"
    exit 1
}

function Rollback {
    Write-Warning-Log "Rolling back to previous version..."
    
    $previousVersion = docker images "${ImageName}" --format "{{.Tag}}" | Select-String -Pattern "^[0-9]" | Select-Object -First 1
    
    if (-not $previousVersion) {
        Write-Error-Log "No previous version found"
        exit 1
    }
    
    $env:IMAGE_TAG = $previousVersion
    docker-compose -f docker-compose.yml up -d --force-recreate
    
    Write-Log "✓ Rolled back to ${previousVersion}"
}

# Main execution
switch ($Action) {
    "build" {
        Build-Image
    }
    "scan" {
        Build-Image
        Security-Scan
    }
    "push" {
        Build-Image
        Push-Image
    }
    "deploy" {
        Build-Image
        Security-Scan
        Push-Image
        Deploy-Compose
        Run-Migrations
        Health-Check
    }
    "migrate" {
        Run-Migrations
    }
    "health" {
        Health-Check
    }
    "rollback" {
        Rollback
    }
    default {
        Write-Error-Log "Unknown action: $Action"
        Write-Host "Usage: .\docker_deploy.ps1 {build|scan|push|deploy|migrate|health|rollback}"
        exit 1
    }
}


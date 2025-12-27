# Schedule automated database backups (PowerShell)
# Run via Task Scheduler: Daily at 2:00 AM

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackupDir = if ($env:BACKUP_DIR) { $env:BACKUP_DIR } else { Join-Path $ScriptDir "..\backups" }
$LogFile = if ($env:BACKUP_LOG_FILE) { $env:BACKUP_LOG_FILE } else { Join-Path $ScriptDir "..\logs\backup.log" }

# Create log directory
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

# Log function
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "Starting scheduled backup"

try {
    # Run backup script
    python "$ScriptDir\backup_database.py" `
        --database-url $env:DATABASE_URL `
        --backup-dir $BackupDir `
        --s3-bucket $env:S3_BACKUP_BUCKET `
        --s3-prefix $env:S3_BACKUP_PREFIX `
        --retention-days $env:BACKUP_RETENTION_DAYS `
        2>&1 | Tee-Object -FilePath $LogFile -Append
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Backup completed successfully"
        exit 0
    }
    else {
        Write-Log "Backup failed with exit code $LASTEXITCODE"
        # Send alert (configure as needed)
        # Send-MailMessage -To "admin@example.com" -Subject "Backup Failed" -Body (Get-Content $LogFile -Raw)
        exit $LASTEXITCODE
    }
}
catch {
    Write-Log "Backup script error: $_"
    exit 1
}

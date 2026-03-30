# run_claude.ps1 - AI Employee Task Scheduler wrapper
param([string]$Skill, [string]$Vault = "D:\fiinal_hackathon_0\AI_Employee_Vault")

Set-Location "D:\fiinal_hackathon_0"
$env:VAULT_PATH = $Vault

try {
    $output = claude --print "/$Skill" 2>&1
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $Vault "Logs\scheduler.log"
    Add-Content -Path $logFile -Value "[$timestamp] $Skill completed"
    if ($output) {
        Add-Content -Path $logFile -Value $output
    }
} catch {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Error "[$timestamp] $Skill failed: $_"
}

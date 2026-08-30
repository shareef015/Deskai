[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Printer','Outlook')][string]$Domain,
    [Parameter(Mandatory=$true)][string]$DeviceId,
    [Parameter(Mandatory=$true)][string]$EvidencePath
)
$ErrorActionPreference = 'Stop'
$observedAt = (Get-Date).ToUniversalTime().ToString('o')
$result = [ordered]@{
    schema_version = 1
    environment = 'staging'
    domain = $Domain
    device_id = $DeviceId
    observed_at = $observedAt
    machine = $env:COMPUTERNAME
    os = (Get-CimInstance Win32_OperatingSystem).Caption
    checks = @()
}
if ($Domain -eq 'Printer') {
    $spooler = Get-Service -Name Spooler
    $result.checks += @{ name='spooler'; status=$spooler.Status.ToString() }
    $printers = @(Get-Printer | Select-Object Name, DriverName, PortName, PrinterStatus)
    $result.printers = $printers
} else {
    $outlook = Get-Process OUTLOOK -ErrorAction SilentlyContinue
    $result.checks += @{ name='outlook_process'; status=($(if ($outlook) {'running'} else {'not_running'})) }
    $result.outlook_process_count = @($outlook).Count
}
$json = $result | ConvertTo-Json -Depth 6
$directory = Split-Path -Parent $EvidencePath
if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
Set-Content -Path $EvidencePath -Value $json -Encoding UTF8
$hash = (Get-FileHash -Algorithm SHA256 -Path $EvidencePath).Hash.ToLowerInvariant()
Write-Output "evidence=$EvidencePath"
Write-Output "sha256=$hash"

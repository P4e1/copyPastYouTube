param(
    [Parameter(Mandatory = $true)][string]$WslIp,
    [Parameter(Mandatory = $true)][int]$Port
)

$ErrorActionPreference = "Stop"

function Test-Page {
    param([int]$LocalPort)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.ReceiveTimeout = 3000
        $client.SendTimeout = 3000
        $client.Connect("127.0.0.1", $LocalPort)
        $stream = $client.GetStream()
        $payload = [Text.Encoding]::ASCII.GetBytes("GET / HTTP/1.1`r`nHost: localhost`r`nConnection: close`r`n`r`n")
        $stream.Write($payload, 0, $payload.Length)
        $buffer = New-Object byte[] 128
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read -le 0) {
            return $false
        }
        $text = [Text.Encoding]::ASCII.GetString($buffer, 0, $read)
        return $text.StartsWith("HTTP/1.1 200") -or $text.StartsWith("HTTP/1.0 200")
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

if (Test-Page -LocalPort $Port) {
    Write-Output "Windows localhost:${Port} already opens the page"
    exit 0
}

$dir = Join-Path $env:LOCALAPPDATA "copypast-youtube"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$pidFile = Join-Path $dir "localhost-relay-$Port.pid"
$outLog = Join-Path $dir "localhost-relay-$Port.out.log"
$errLog = Join-Path $dir "localhost-relay-$Port.err.log"
if (Test-Path $pidFile) {
    $old = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($old) {
        Stop-Process -Id ([int]$old) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 300
}

$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Windows has no py launcher, localhost relay was not started"
    exit 1
}

$relay = Join-Path $PSScriptRoot "windows_localhost_relay.py"
$relayArgs = @(
    "-3", $relay,
    "--listen", "127.0.0.1",
    "--listen-port", "$Port",
    "--target", $WslIp,
    "--target-port", "$Port"
)
$proc = Start-Process -FilePath $py.Source -ArgumentList $relayArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
Set-Content -Path $pidFile -Value $proc.Id

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 200
    if (Test-Page -LocalPort $Port) {
        Write-Output "Windows localhost:${Port} forwards to ${WslIp}:${Port}"
        exit 0
    }
}

Write-Error "Windows localhost:${Port} still does not open the page. Log: $errLog"
exit 1

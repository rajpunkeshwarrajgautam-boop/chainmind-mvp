# Verifies production API host, Vercel /api rewrite, and CORS preflight.
# Usage:
#   .\scripts\verify_vercel_api_connectivity.ps1
#   .\scripts\verify_vercel_api_connectivity.ps1 -ApiOrigin "https://your-api.example.com"

param(
    [string]$WebOrigin = "https://chainmind-mvp-web.vercel.app",
    [string]$ApiOrigin = "https://chainmind-mvp.onrender.com"
)

$ErrorActionPreference = "Stop"

function Get-ResponseOrNull {
    param([string]$Uri, [string]$Method = "GET", [hashtable]$Headers = @{})
    try {
        return Invoke-WebRequest -Uri $Uri -Method $Method -UseBasicParsing -TimeoutSec 45 -Headers $Headers
    } catch {
        return $_.Exception.Response
    }
}

Write-Host "`n== API host $ApiOrigin /health ==" -ForegroundColor Cyan
$health = Get-ResponseOrNull -Uri "$ApiOrigin/health"
if ($null -eq $health) {
    Write-Host "FAIL: no response" -ForegroundColor Red
    exit 1
}
$routing = $health.Headers["x-render-routing"]
$code = [int]$health.StatusCode
Write-Host "HTTP $code; x-render-routing: $routing"
if ($routing -eq "no-server") {
    Write-Host @"

FAIL: Render reports no web service at this hostname.
Set Vercel API_ORIGIN and NEXT_PUBLIC_API_ORIGIN to a live API URL, redeploy the web app,
and deploy the API (e.g. Render Blueprint from render.yaml) if you intend to use Render.

"@ -ForegroundColor Red
    exit 1
}
if ($code -ne 200) {
    Write-Host "FAIL: expected 200 from /health, got $code" -ForegroundColor Red
    exit 1
}
Write-Host "OK: $($health.Content.Substring(0, [Math]::Min(160, $health.Content.Length)))" -ForegroundColor Green

Write-Host "`n== CORS preflight (OPTIONS, Origin: $WebOrigin) ==" -ForegroundColor Cyan
$opt = Get-ResponseOrNull -Uri "$ApiOrigin/api/v1/signals/weather-sample" -Method OPTIONS -Headers @{
    "Origin"                         = $WebOrigin
    "Access-Control-Request-Method"  = "GET"
    "Access-Control-Request-Headers" = "content-type"
}
$oc = [int]$opt.StatusCode
$aco = $opt.Headers["Access-Control-Allow-Origin"]
Write-Host "OPTIONS -> $oc; Access-Control-Allow-Origin: $aco"
if ($oc -lt 200 -or $oc -gt 299) {
    Write-Host "FAIL: OPTIONS status $oc" -ForegroundColor Red
    exit 1
}
if (-not $aco) {
    Write-Host "WARN: no Allow-Origin on OPTIONS (same-origin /api rewrites may still work)." -ForegroundColor Yellow
} else {
    Write-Host "OK" -ForegroundColor Green
}

Write-Host "`n== Vercel rewrite $WebOrigin/api/v1/signals/weather-sample ==" -ForegroundColor Cyan
$vx = Get-ResponseOrNull -Uri "$WebOrigin/api/v1/signals/weather-sample"
$vc = [int]$vx.StatusCode
Write-Host "GET -> $vc"
if ($vc -ne 200) {
    Write-Host "FAIL: Vercel rewrite or upstream API error" -ForegroundColor Red
    exit 1
}
Write-Host "OK: $($vx.Content.Substring(0, [Math]::Min(160, $vx.Content.Length)))" -ForegroundColor Green

Write-Host "`nAll checks passed." -ForegroundColor Green
exit 0

# Коротко: скрипт автоматизує локальну перевірку для smoke-new-stack.

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Email = "client@example.com",
    [string]$Password = "Password123!"
)

$ErrorActionPreference = "Stop"

$cookieJar = Join-Path $env:TEMP "fcms-smoke-cookies.txt"
if (Test-Path $cookieJar) {
    Remove-Item $cookieJar -Force
}

function Invoke-Curl {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [string]$Method = "GET",
        [string[]]$Headers = @(),
        [string]$Body = "",
        [int]$ExpectedStatus = 200,
        [string]$Label = "request"
    )

    $tempBody = Join-Path $env:TEMP ("fcms-smoke-body-" + [guid]::NewGuid().ToString() + ".txt")
    $tempRequest = Join-Path $env:TEMP ("fcms-smoke-request-" + [guid]::NewGuid().ToString() + ".txt")
    try {
        $args = @(
            "--silent",
            "--show-error",
            "--location",
            "--output", $tempBody,
            "--write-out", "%{http_code}",
            "--cookie", $cookieJar,
            "--cookie-jar", $cookieJar,
            "-X", $Method
        )

        foreach ($header in $Headers) {
            $args += @("-H", $header)
        }

        if ($Body) {
            Set-Content -Path $tempRequest -Value $Body -NoNewline
            $args += @("--data-binary", "@$tempRequest")
        }

        $args += $Url
        $statusCode = & curl.exe @args

        if ([int]$statusCode -ne $ExpectedStatus) {
            $body = if (Test-Path $tempBody) { Get-Content $tempBody -Raw } else { "" }
            throw "$Label failed. Expected status $ExpectedStatus but got $statusCode. Body: $body"
        }

        if (Test-Path $tempBody) {
            return Get-Content $tempBody -Raw
        }

        return ""
    }
    finally {
        if (Test-Path $tempBody) {
            Remove-Item $tempBody -Force
        }
        if (Test-Path $tempRequest) {
            Remove-Item $tempRequest -Force
        }
    }
}

Write-Host "Checking live health..."
$null = Invoke-Curl -Url "$BaseUrl/health/live" -ExpectedStatus 200 -Label "health/live"

Write-Host "Checking ready health..."
$null = Invoke-Curl -Url "$BaseUrl/health/ready" -ExpectedStatus 200 -Label "health/ready"

Write-Host "Logging in demo user..."
$loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json -Compress
$null = Invoke-Curl `
    -Url "$BaseUrl/auth/login" `
    -Method "POST" `
    -Headers @("Content-Type: application/json") `
    -Body $loginBody `
    -ExpectedStatus 200 `
    -Label "auth/login"

if (-not (Test-Path $cookieJar)) {
    throw "Cookie jar was not created."
}

$csrfLine = Get-Content $cookieJar | Where-Object { $_ -match "fcms_csrf_token" } | Select-Object -First 1
if (-not $csrfLine) {
    throw "CSRF cookie was not issued after login."
}
$csrfToken = ($csrfLine -split "\s+")[-1]

Write-Host "Checking current user..."
$null = Invoke-Curl -Url "$BaseUrl/auth/me" -ExpectedStatus 200 -Label "auth/me"

Write-Host "Checking schedules..."
$null = Invoke-Curl -Url "$BaseUrl/schedules" -ExpectedStatus 200 -Label "schedules"

Write-Host "Checking client subscriptions..."
$null = Invoke-Curl -Url "$BaseUrl/subscriptions/my-subscriptions" -ExpectedStatus 200 -Label "subscriptions/my-subscriptions"

Write-Host "Logging out..."
$null = Invoke-Curl `
    -Url "$BaseUrl/auth/logout" `
    -Method "POST" `
    -Headers @("X-CSRF-Token: $csrfToken") `
    -ExpectedStatus 204 `
    -Label "auth/logout"

Write-Host "Smoke test passed." -ForegroundColor Green

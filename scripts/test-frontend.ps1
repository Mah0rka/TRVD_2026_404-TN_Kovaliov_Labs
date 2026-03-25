# Коротко: скрипт автоматизує локальну перевірку для test-frontend.

$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
    npm run test:coverage
}
finally {
    Pop-Location
}

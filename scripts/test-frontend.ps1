$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
    npm run test:coverage
}
finally {
    Pop-Location
}

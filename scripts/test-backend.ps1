$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\backend"
try {
    python -m pytest --cov=app --cov-report=term-missing
}
finally {
    Pop-Location
}

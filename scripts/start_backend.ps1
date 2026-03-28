param(
    [string]$ListenHost = "127.0.0.1",
    [int]$ListenPort = 8000,
    [switch]$Reload,
    [switch]$SkipMigrations
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $PSScriptRoot "run_backend.py"

function Test-PythonCandidate {
    param(
        [string]$Command,
        [string[]]$BaseArgs = @()
    )

    try {
        if ($Command -like "*.exe" -and -not (Test-Path $Command)) {
            return $false
        }

        & $Command @BaseArgs "-c" "import pydantic, uvicorn, alembic" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

$candidates = @(
    @{
        Label = ".venv"
        Command = (Join-Path $projectRoot ".venv\Scripts\python.exe")
        Args = @()
    },
    @{
        Label = "py -3.11"
        Command = "py"
        Args = @("-3.11")
    },
    @{
        Label = "py -3"
        Command = "py"
        Args = @("-3")
    },
    @{
        Label = "python"
        Command = "python"
        Args = @()
    }
)

$selected = $null
foreach ($candidate in $candidates) {
    if (Test-PythonCandidate -Command $candidate.Command -BaseArgs $candidate.Args) {
        $selected = $candidate
        break
    }
}

if (-not $selected) {
    Write-Error "No suitable Python interpreter found for Muni-Pal. Install project dependencies or recreate .venv."
    exit 1
}

$srcPath = Join-Path $projectRoot "src"
if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$srcPath;$env:PYTHONPATH"
}
else {
    $env:PYTHONPATH = $srcPath
}

$argList = @()
$argList += $selected.Args
$argList += $launcher
$argList += "--host"
$argList += $ListenHost
$argList += "--port"
$argList += [string]$ListenPort

if ($Reload) {
    $argList += "--reload"
}

if ($SkipMigrations) {
    $argList += "--skip-migrations"
}

Write-Host "[munipal] Using Python candidate: $($selected.Label)" -ForegroundColor Cyan
& $selected.Command @argList
exit $LASTEXITCODE

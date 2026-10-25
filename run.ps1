<#
.SYNOPSIS
Starts the local Dymo Print UI without Poetry or a project virtual environment.

.DESCRIPTION
Initializes the dymo-bluetooth submodule if absent and installs frontend
dependencies with npm ci. By default, rebuilds frontend/dist and starts the
application at http://127.0.0.1:8000, opening the browser automatically.

Runs Python 3.11 through uvx with this checkout installed in editable mode.
Python edits are picked up on the next launch; package metadata is refreshed
on each launch. uv manages the Python environment and can download Python.

All paths are resolved relative to this script, regardless of the caller's
working directory. The caller's location is restored when the script exits.
Stop the server with Ctrl+C.

.PARAMETER Dev
Starts the backend with automatic Python reload instead of building and serving
the production UI. Installs frontend dependencies but does not open a browser.
Run npm --prefix frontend run dev from the repository root in a second terminal
and open http://localhost:5173.

.EXAMPLE
.\run.ps1

Installs dependencies, builds the frontend, and opens the production UI.

.EXAMPLE
.\run.ps1 -Dev

Starts the backend with automatic reload for development alongside Vite.

.EXAMPLE
Get-Help .\run.ps1 -Full

Displays the full launcher documentation without starting the application.

.INPUTS
None. This script does not accept pipeline input.

.OUTPUTS
None. Dependency installation, build, and server logs are written to the console.

.NOTES
Requires uv (uvx), Node.js with npm, and Git when initializing the submodule.
No Poetry installation or virtual environment activation is required.
Installation and build failures terminate the script before starting the server.
On normal server termination, the script returns the server's exit code.
#>
[CmdletBinding()]
param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

foreach ($command in @("uvx", "npm")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found. Install uv and Node.js (with npm), then retry."
    }
}

Push-Location $PSScriptRoot
try {
    if (-not (Test-Path "external\dymo-bluetooth\dymo_bluetooth\__init__.py")) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            throw "Git is required to initialize the dymo-bluetooth submodule."
        }
        & git submodule update --init -- external/dymo-bluetooth
        if ($LASTEXITCODE -ne 0) {
            throw "Could not initialize the dymo-bluetooth submodule."
        }
    }

    & npm --prefix frontend ci
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend dependency installation failed."
    }

    $uvxArguments = @(
        "--python", "3.11",
        "--from", ".",
        "--with-editable", ".",
        "--refresh-package", "dymo-print-ui"
    )

    if ($Dev) {
        & uvx @uvxArguments uvicorn dymo_print_ui.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir src
    }
    else {
        & npm --prefix frontend run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed."
        }
        & uvx @uvxArguments dymo-print-ui
    }
    $serverExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $serverExitCode

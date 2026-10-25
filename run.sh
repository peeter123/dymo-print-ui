#!/usr/bin/env bash
#
# Starts the local Dymo Print UI without Poetry or a project virtual environment.
#
# Initializes the dymo-bluetooth submodule if absent and installs frontend
# dependencies with npm ci. By default, rebuilds frontend/dist and starts the
# application at http://127.0.0.1:8000, opening the browser automatically.
#
# Runs Python 3.11 through uvx with this checkout installed in editable mode.
# Python edits are picked up on the next launch; package metadata is refreshed
# on each launch. uv manages the Python environment and can download Python.
#
# All paths are resolved relative to this script, regardless of the caller's
# working directory. Stop the server with Ctrl+C.
#
# Requires uv (uvx), Node.js with npm, and Git when initializing the submodule.
# Installation and build failures terminate the script before starting the
# server. On normal server termination, the script returns the server's exit code.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./run.sh [--dev] [--help]

Starts the local Dymo Print UI without Poetry or a project virtual environment.

Options:
  --dev     Start the backend with automatic Python reload instead of building
            and serving the production UI. Installs frontend dependencies but
            does not open a browser. Run `npm --prefix frontend run dev` from the
            repository root in a second terminal and open http://localhost:5173.
  -h, --help
            Show this help without starting the application.

Examples:
  ./run.sh          Install dependencies, build the frontend, open the UI.
  ./run.sh --dev    Start the backend with automatic reload alongside Vite.
EOF
}

dev=false
for arg in "$@"; do
    case "$arg" in
        --dev) dev=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

for command in uvx npm; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Required command '$command' was not found. Install uv and Node.js (with npm), then retry." >&2
        exit 1
    fi
done

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -f external/dymo-bluetooth/dymo_bluetooth/__init__.py ]]; then
    if ! command -v git >/dev/null 2>&1; then
        echo "Git is required to initialize the dymo-bluetooth submodule." >&2
        exit 1
    fi
    git submodule update --init -- external/dymo-bluetooth \
        || { echo "Could not initialize the dymo-bluetooth submodule." >&2; exit 1; }
fi

npm --prefix frontend ci \
    || { echo "Frontend dependency installation failed." >&2; exit 1; }

uvx_arguments=(
    --python 3.11
    --from .
    --with-editable .
    --refresh-package dymo-print-ui
)

if [[ "$dev" == true ]]; then
    exec uvx "${uvx_arguments[@]}" uvicorn dymo_print_ui.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir src
else
    npm --prefix frontend run build \
        || { echo "Frontend build failed." >&2; exit 1; }
    exec uvx "${uvx_arguments[@]}" dymo-print-ui
fi

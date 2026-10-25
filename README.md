# dymo-print-ui

A local, browser-based label editor for the **Dymo LetraTag 200B**.

Design your label in the browser — text in any Google Font, Material Design
Icons, and simple shapes — preview it exactly as it will print, and send it to
the printer over Bluetooth LE.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/),
Node.js (with npm), and Git. Clone the repository, then run from PowerShell:

```powershell
.\run.ps1
```

or on Ubuntu / Linux, from bash:

```bash
./run.sh
```

The launcher initializes the driver submodule if needed, runs `npm ci` and
`npm run build`, then starts the app at **http://127.0.0.1:8000** and opens your
browser. No Poetry installation, activated virtual environment, or project
`.venv` is needed: `uvx` manages an isolated environment in uv's cache.
Python 3.11 is selected automatically (uv can download it if necessary).

The script works from any working directory. It installs this checkout in
**editable mode**, so Python source changes are picked up on the next launch
instead of running a cached copy. It also refreshes the app installation on each
launch so changes to `pyproject.toml` are picked up.

For parameter documentation and examples, use `Get-Help .\run.ps1 -Full` or
`./run.sh --help`. Both launchers behave identically.

### Manual uvx launch

From the repository root:

```powershell
git submodule update --init -- external/dymo-bluetooth
npm --prefix frontend ci
npm --prefix frontend run build
uvx --python 3.11 --from . --with-editable . --refresh-package dymo-print-ui dymo-print-ui
```

Stop the server with Ctrl+C and rerun after backend changes. Rebuild the frontend
after frontend changes, or use development mode below.

### Poetry alternative

The existing Poetry workflow remains supported:

```powershell
git submodule update --init -- external/dymo-bluetooth
poetry install
npm --prefix frontend ci
npm --prefix frontend run build
poetry run dymo-print-ui
```

## Development

Run two processes in separate terminals, both starting in the repository root:

```powershell
.\run.ps1 -Dev                 # backend on :8000, reloads Python changes
```

```bash
./run.sh --dev                 # same, on Ubuntu / Linux
```

```powershell
npm --prefix frontend run dev  # Vite on :5173 (open this)
```

`-Dev` (`--dev` for `run.sh`) installs the frontend dependencies but skips the production frontend build
and automatic browser opening. Vite updates the UI as you edit and proxies
`/api` to the backend. Without the launcher, the equivalent backend command is:

```powershell
uvx --python 3.11 --from . --with-editable . --refresh-package dymo-print-ui uvicorn dymo_print_ui.app:app --host 127.0.0.1 --port 8000 --reload --reload-dir src
```

## Frontend assets and packaging

`uvx` installs Python packages; it **does not run npm or build the frontend**.
The production server reads `frontend/dist` from this checkout. That directory
is generated locally and ignored by Git; `run.ps1` rebuilds it on every normal
launch so it cannot silently serve a stale build after source changes.
The backend also needs `frontend/node_modules/@mdi/svg` for icon search and SVG
data, even when the UI is already built. Keep both directories.

The current Python package does **not bundle** the frontend build or MDI data.
Use the local editable command above, not a standalone
`uvx --from git+https://github.com/peeter123/dymo-print-ui dymo-print-ui` install.
A standalone wheel/Git launch would require bundling those assets into the
Python package and changing the backend to locate the packaged files.

## Driver dependency

The `external/dymo-bluetooth` submodule is **still required by the current setup**.
The app adds it to `sys.path`, while `pyproject.toml` declares its runtime
dependencies (`bleak` and `pillow`). `run.ps1` initializes it on first use.

A proper Git dependency on `dymo-bluetooth` can replace the submodule; it is not
necessary to keep both. Pin that dependency to a commit for reproducibility,
remove the `sys.path` injection, and remove the submodule registration and
checkout. Simply adding a Git dependency without removing the injection would
still let an existing submodule override the installed driver. This launcher
keeps the existing driver setup rather than changing dependency management.

See [CLAUDE.md](CLAUDE.md) for architecture and the driver gotchas.

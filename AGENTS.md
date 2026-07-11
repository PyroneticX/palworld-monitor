# Palworld monitor

Uses `uv` for dependencies and commands. See [README.md](README.md) for user-facing setup, usage, and the full command-line flag reference.

## Commands

- `uv sync` — create `.venv` and install deps
- `uv run poe start` — start the app (`src/main.py`)
- `uv run poe test` — run all tests
- `uv run poe test test/test_file.py` — single file
- `uv run poe smoke` — run smoke tests (e2e tests in `test/e2e/`)
- `uv run poe lint` — ruff check
- `uv run poe format` — ruff format
- `uv run poe build-exe` — build a single-file Windows exe into `dist/`

## Configuration

- `src/settings.yaml` (gitignored) — copy from `src/settings.yaml.example`
- Nested YAML domains (`palserver`, `web`, `features`, `autoStop`, `security`) get mapped to flat keys in `src/settings.py`
- `palserver.pollingRate` (default 5s) controls how often the app polls the server for status/players and how often the detection loop runs
- `palserver.exePath` can be a bare command name (e.g. `python`) — validation uses `shutil.which`
- `session_secret.key` is auto-generated at first run and gitignored
- PID files (`palworld_server.win.pid`, `palworld_server.linux.pid`) are gitignored
- CLI flags (`src/cli.py`) override `settings.yaml` values. `dest` names map 1:1 to the flat keys in `Settings`. `--no-*` flags use `action="store_false"` with `default=None` so they only override when explicitly passed (won't clobber a YAML `false`). Passwords are masked in override logs.

## Architecture

- **Entrypoint:** `src/main.py` is a thin orchestrator. It imports from:
  - `src/cli.py` — `parse_args()` / `apply_overrides()` (argparse). Testable in isolation.
  - `src/setup_wizard.py` — first-run interactive setup, auto-detection, PalServer REST API config. All functions are public and importable for testing.
- `PalWorldController` (orchestrator) → `AutoStartManager` (UDP listener) + `WebServer` (Flask thread)
- `AutoStartManager` binds a UDP socket on the Palworld game port and sniffs for `\x09\x08\x00` (first client packet) to trigger `start_server()`
- Process control (`src/process_manager.py`): `WindowsProcessManager` / `LinuxProcessManager` via psutil.
  - `find_process_pid` checks process name, exe path, and `cmdline` for a match
- `PalWorldController` runs a background detection loop (every `pollingRate` s) that discovers a PalServer process that started independently of the monitor
- Server communication (`src/api_clients.py`): `RestClient` (default, recommended) or `RconClient` (legacy).
- Flask runs in the main thread. Ctrl+C shuts down the server cleanly; daemon threads (AutoStartManager,
detection loops) exit automatically with the interpreter.
- **Live updates:** the dashboard uses Server-Sent Events (`/stream` endpoint) to push status changes in real time instead of polling

## Testing

- pytest config in `pyproject.toml`: `-v`, `--tb=short`, `--capture=no`
- Linux tests (`@pytest.mark.linux`) skipped on Windows and vice versa.
- Test factories in `test/support/`, fixtures in `test/conftest.py`.
- Smoke tests: run with `uv run poe smoke` — these are end-to-end tests in `test/e2e/` that verify the web server works correctly.
  - No real PalServer needed — `test/e2e/dummy/PalServer-Dummy.py` serves a minimal REST API mimicking the real server
  - **Destructive**: the test helpers kill any existing PalServer process and free ports 8211–8213 at startup and teardown. Do NOT run on a machine running a real PalServer.
  - `DUMMY_PLAYER_COUNT` env var controls how many fake players the dummy reports (default 3, set to 0 for autostop tests)

### Manual integration test checklist

The e2e suite uses a mock REST API — it doesn't exercise a real PalServer.
Before shipping, verify these against an actual running server:

- [ ] **Startup detection** — stop PalServer, start the monitor. It should auto-detect the server path.
- [ ] **Auto-start** — stop PalServer. Have a friend try to connect from their game client. The monitor should detect the UDP probe and start PalServer.
- [ ] **Player tracking** — join the server with a real client. The web dashboard should show your player name, level, and online status.
- [ ] **Auto-stop** — all players leave. The server should stop after the configured delay.
- [ ] **Kick** — from the web UI, kick a player. They should be disconnected.
- [ ] **Ban** — ban a player via Steam ID. They should be unable to rejoin.
- [ ] **Wrong admin password** — start the monitor with an incorrect `adminPassword` in `settings.yaml`. The dashboard should show the server as offline.
- [ ] **RCON** (if supported) — set `protocol: "RCON"`, verify player count and kick/ban work.

## Constraints

- Must run on the same host as the Palworld server (needs process spawn/kill access).
- Only `pytest` for CI (`uv sync`). No linter/typecheck step.

## Build & Distribution

- **Prebuilt binaries**: pushing a `v*` tag triggers `.github/workflows/release.yml`, which builds on `windows-latest` and `ubuntu-latest`, publishing both `palworld-monitor.exe` and `palworld-monitor` (Linux) to a GitHub Release.
- **Local build**: `uv run poe build-exe` runs `build_exe.py` (PyInstaller via `palworld-monitor.spec`), then copies `src/settings.yaml.example` → `dist/settings.yaml` so the dist folder is runnable as-is.
- **PyInstaller spec** (`palworld-monitor.spec`): bundles `src/templates`, `src/static`, and `src/settings.yaml.example` as data. Hidden imports: `flask_limiter`, `flask_login`, `flask_wtf`, `psutil`, `rcon`.
- **Frozen-mode paths**: when running the exe, `sys.frozen` is set. `src/main.py` `_determine_settings_path()` resolves `settings.yaml` next to the exe (`os.path.dirname(sys.executable)`); `src/web_server.py` resolves templates/static from `sys._MEIPASS`. When touching path resolution, account for both frozen and non-frozen modes.
- **No `exit()`**: use `sys.exit()` — PyInstaller doesn't inject the `exit` builtin that CPython's interactive mode does.
- **Web UI link**: `src/setup_wizard.py` `print_web_link()` prints `http://localhost:{port}` and the LAN IP to the console before the Flask server starts (it blocks).

## Palworld REST API reference

When modifying `src/api_clients.py` or `test/e2e/dummy/PalServer-Dummy.py`,
always consult the official API docs first:

- [REST API overview](https://docs.palworldgame.com/category/rest-api)
- [Get server info](https://docs.palworldgame.com/api/rest-api/info) — `GET /v1/api/info`
- [Get player list](https://docs.palworldgame.com/api/rest-api/players) — `GET /v1/api/players`
- [Get server settings](https://docs.palworldgame.com/api/rest-api/settings) — `GET /v1/api/settings`
- [Announce](https://docs.palworldgame.com/api/rest-api/announce) — `POST /v1/api/announce`
- [Kick player](https://docs.palworldgame.com/api/rest-api/kick) — `POST /v1/api/kick`
- [Ban player](https://docs.palworldgame.com/api/rest-api/ban) — `POST /v1/api/ban`
- [Unban player](https://docs.palworldgame.com/api/rest-api/unban) — `POST /v1/api/unban`
- [Save the world](https://docs.palworldgame.com/api/rest-api/save) — `POST /v1/api/save`
- [Shutdown the server](https://docs.palworldgame.com/api/rest-api/shutdown) — `POST /v1/api/shutdown`
- [Force stop the server](https://docs.palworldgame.com/api/rest-api/stop) — `POST /v1/api/stop`
- [Get world actor snapshot](https://docs.palworldgame.com/api/rest-api/game-data) — `GET /v1/api/game-data`
- [Get server metrics](https://docs.palworldgame.com/api/rest-api/metrics) — `GET /v1/api/metrics`

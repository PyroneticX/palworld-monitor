# Palworld monitor

Uses `uv` for dependencies and commands.

## Commands

- `uv sync` — create `.venv` and install deps
- `uv run poe run` — start the app (`src/main.py`)
- `uv run poe test` — run all tests
- `uv run poe test test/test_file.py` — single file
- `uv run poe smoke` — run smoke tests (e2e tests in `test/e2e/`)
- `uv run poe lint` — ruff check
- `uv run poe format` — ruff format

## Configuration

- `src/settings.yaml` (gitignored) — copy from `src/settings.yaml.example`
- Nested YAML domains (`palserver`, `web`, `features`, `autoStop`, `security`) get mapped to flat keys in `src/settings.py`
- `palserver.pollingRate` (default 5s) controls how often the app polls the server for status/players and how often the detection loop runs
- `palserver.exePath` can be a bare command name (e.g. `python`) — validation uses `shutil.which`
- `session_secret.key` is auto-generated at first run and gitignored
- PID files (`palworld_server.win.pid`, `palworld_server.linux.pid`) are gitignored

## Architecture

- **Entrypoint:** `src/main.py` wires: `PalWorldController` (orchestrator) → `AutoStartManager` (UDP listener) + `WebServer` (Flask thread)
- `AutoStartManager` binds a UDP socket on the Palworld game port and sniffs for `\x09\x08\x00` (first client packet) to trigger `start_server()`
- Process control (`src/process_manager.py`): `WindowsProcessManager` / `LinuxProcessManager` via psutil.
  - `find_process_pid` checks process name, exe path, and `cmdline` for a match
- `PalWorldController` runs a background detection loop (every `pollingRate` s) that discovers a PalServer process that started independently of the monitor
- Server communication (`src/api_clients.py`): `RestClient` (default, recommended) or `RconClient` (legacy).
- Flask runs in a daemon thread (not the main thread).
- **Live updates:** the dashboard uses Server-Sent Events (`/stream` endpoint) to push status changes in real time instead of polling

## Testing

- pytest config in `pyproject.toml`: `-v`, `--tb=short`, `--capture=no`
- Linux tests (`@pytest.mark.linux`) skipped on Windows and vice versa.
- Test factories in `test/support/`, fixtures in `test/conftest.py`.
- Smoke tests: run with `uv run poe smoke` — these are end-to-end tests in `test/e2e/` that verify the web server works correctly.
  - No real PalServer needed — `test/e2e/dummy/PalServer-Dummy.py` serves a minimal REST API mimicking the real server
  - `DUMMY_PLAYER_COUNT` env var controls how many fake players the dummy reports (default 3, set to 0 for autostop tests)

## Constraints

- Must run on the same host as the Palworld server (needs process spawn/kill access).
- Only `pytest` for CI (`uv sync`). No linter/typecheck step.

## Palworld REST API reference

When modifying `src/api_clients.py` or `test/e2e/dummy/PalServer-Dummy.py`,
always consult the official API docs first:

- [REST API overview](https://docs.palworldgame.com/category/rest-api)
- [Get server info](https://docs.palworldgame.com/api/rest-api/info) — `GET /v1/api/info`
- [Get player list](https://docs.palworldgame.com/api/rest-api/players) — `GET /v1/api/players`
- [Get server metrics](https://docs.palworldgame.com/api/rest-api/metrics) — `GET /v1/api/metrics`
- [Get server settings](https://docs.palworldgame.com/api/rest-api/settings) — `GET /v1/api/settings`
- [Announce](https://docs.palworldgame.com/api/rest-api/announce) — `POST /v1/api/announce`
- [Kick player](https://docs.palworldgame.com/api/rest-api/kick) — `POST /v1/api/kick`
- [Ban player](https://docs.palworldgame.com/api/rest-api/ban) — `POST /v1/api/ban`
- [Unban player](https://docs.palworldgame.com/api/rest-api/unban) — `POST /v1/api/unban`

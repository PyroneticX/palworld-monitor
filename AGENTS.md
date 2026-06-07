# Palworld monitor

Uses the venv's Python, not a system install.

## Commands

- `make run` — start the app (`src/main.py`)
- `make test` — run all tests
- `make setup` — create venv + `pip install -r requirements.txt`
- `.venv\Scripts\python.exe -m pytest test/test_file.py -v` — single file
- `.venv\Scripts\ruff.exe check src/ test/` — lint
- `.venv\Scripts\ruff.exe format src/ test/` — format

## Configuration

- `src/settings.yaml` (gitignored) — copy from `src/settings.yaml.example`
- Nested YAML domains (`palserver`, `web`, `features`, `autoStop`, `security`) get mapped to flat keys in `src/settings.py`
- `session_secret.key` is auto-generated at first run and gitignored
- PID files (`palworld_server.win.pid`, `palworld_server.linux.pid`) are gitignored

## Architecture

- **Entrypoint:** `src/main.py` wires: `PalWorldController` (orchestrator) → `AutoStartManager` (UDP listener) + `WebServer` (Flask thread)
- `AutoStartManager` binds a UDP socket on the Palworld game port and sniffs for `\x09\x08\x00` (first client packet) to trigger `start_server()`
- Process control (`src/process_manager.py`): `WindowsProcessManager` / `LinuxProcessManager` via psutil.
- Server communication (`src/api_clients.py`): `RestClient` (default, recommended) or `RconClient` (legacy).
- Flask runs in a daemon thread (not the main thread).

## Testing

- pytest config in `pytest.ini`: `-v`, `--tb=short`, `--capture=no`
- Linux tests (`@pytest.mark.linux`) skipped on Windows and vice versa.
- Test factories in `test/support/`, fixtures in `test/conftest.py`.

## Constraints

- Must run on the same host as the Palworld server (needs process spawn/kill access).
- Only `pytest` for CI (`pip install -r requirements.txt`). No linter/typecheck step.

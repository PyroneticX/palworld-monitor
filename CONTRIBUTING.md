# Contributing to Palworld Monitor

## Development Setup

```bash
git clone https://github.com/kevinnio/palworld-monitor.git
cd palworld-monitor
uv sync
```

## Running Tests

**Unit tests** (no external dependencies):

```bash
uv run poe test
```

**Linting and formatting:**

```bash
uv run poe lint
uv run poe format
```

## Smoke Tests (E2E)

Smoke tests launch the real app and exercise it through a headless browser.
They require a local Palworld server installation and are not run in CI.

### Setup

1. Copy the example settings and edit to match your environment:

   ```bash
   cp test/e2e/settings.yaml.example test/e2e/settings.yaml
   ```

   At minimum, set `palserver.exePath` to your PalServer executable.

2. Run the smoke suite:

   ```bash
   uv run poe smoke
   ```

   To run in headed (visible browser) mode for debugging:

   ```bash
   SMOKE_HEADLESS=0 uv run poe smoke
   ```

### What the smoke tests do

1. Start the monitor app on port 8213.
2. Log in via the web UI and verify the dashboard renders.
3. Start the Palworld server through the UI, confirm the status turns ON.
4. Stop the server through the UI, confirm the status turns OFF.

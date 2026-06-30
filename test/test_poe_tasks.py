import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Try to find uv executable (installed via winget or other methods)
UV_CANDIDATES = [
    Path(sys.executable).with_name("uv.exe" if sys.platform == "win32" else "uv"),
    Path(
        __import__("os").path.join(
            __import__("os").environ["USERPROFILE"],
            "AppData",
            "Local",
            "Microsoft",
            "WinGet",
            "Packages",
            "astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe",
            "uv.exe" if sys.platform == "win32" else "uv",
        )
    ),
]

UV = next((p for p in UV_CANDIDATES if p.exists()), None)
POE_TASKS = ("run", "test", "lint", "format")


def _run_poe(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(UV), "run", "poe", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_poe_tasks_are_configured():
    assert UV is not None, "uv not found; install via winget or add to PATH"

    result = _run_poe("--help")
    output = result.stdout + result.stderr

    assert result.returncode == 0, output

    for task in POE_TASKS:
        assert task in output, f"task {task!r} missing from poe --help"


def test_poe_tasks_dry_run():
    assert UV is not None, "uv not found; install via winget or add to PATH"

    for task in POE_TASKS:
        result = _run_poe("-d", task)
        output = result.stdout + result.stderr

        assert result.returncode == 0, f"poe -d {task} failed:\n{output}"

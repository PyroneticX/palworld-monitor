import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UV = shutil.which("uv")
POE_TASKS = ("run", "test", "lint", "format")


def _run_poe(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [UV, "run", "poe", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_poe_tasks_are_configured():
    assert UV is not None, "uv not found; add it to PATH"

    result = _run_poe("--help")
    output = result.stdout + result.stderr

    assert result.returncode == 0, output

    for task in POE_TASKS:
        assert task in output, f"task {task!r} missing from poe --help"


def test_poe_tasks_dry_run():
    assert UV is not None, "uv not found; add it to PATH"

    for task in POE_TASKS:
        result = _run_poe("-d", task)
        output = result.stdout + result.stderr

        assert result.returncode == 0, f"poe -d {task} failed:\n{output}"

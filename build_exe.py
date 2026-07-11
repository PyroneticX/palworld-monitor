import subprocess, sys

subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "palworld-monitor.spec"], check=True)
print("Build complete. dist/ contains: palworld-monitor.exe")

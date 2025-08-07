import subprocess
import psutil
import os
from settings import settings

class OSProcessManager:
    def __init__(self):
        self.launched_pid = None
        self._load_pid_from_file()
        # If there is no PID file, try to detect an already running Palworld server
        if self.launched_pid is None and not os.path.exists(self.pid_file_name()):
            self._detect_existing_process_from_settings()

    def pid_file_name(self):
        raise NotImplementedError

    def _after_launch(self, process):
        self.launched_pid = process.pid
        self._save_pid_to_file(process.pid)

    def _save_pid_to_file(self, pid):
        try:
            with open(self.pid_file_name(), 'w') as f:
                f.write(str(pid))
        except Exception:
            pass

    def _load_pid_from_file(self):
        if os.path.exists(self.pid_file_name()):
            try:
                with open(self.pid_file_name(), 'r') as f:
                    pid = int(f.read().strip())
                    self.launched_pid = pid
            except Exception:
                self.launched_pid = None

    def _remove_pid_file(self):
        if os.path.exists(self.pid_file_name()):
            try:
                os.remove(self.pid_file_name())
            except Exception:
                pass

    def _detect_existing_process_from_settings(self):
        """Detect a running Palworld server process and persist its PID.

        Strategy:
        - Prefer matching by the executable basename from settings.palworldServerExePath
        - Fallback to settings.palworldMainProcessName
        - Also check full exe path and cmdline where possible
        """
        try:
            candidates = set()
            exe_path = getattr(settings, 'palworldServerExePath', None)
            main_name = getattr(settings, 'palworldMainProcessName', None)

            if exe_path:
                candidates.add(os.path.basename(exe_path).lower())
            if main_name:
                candidates.add(main_name.lower())

            if not candidates and not exe_path:
                return

            for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cmdline']):
                try:
                    info = proc.info
                    name = (info.get('name') or '').lower()
                    exe = (info.get('exe') or '').lower()
                    exe_base = os.path.basename(exe) if exe else ''
                    cmdline_list = info.get('cmdline') or []
                    cmdline = ' '.join(map(str, cmdline_list)).lower()

                    matched = False
                    if name in candidates or exe_base in candidates:
                        matched = True
                    elif exe_path:
                        low_path = exe_path.lower()
                        if exe == low_path or low_path in cmdline:
                            matched = True

                    if matched:
                        self.launched_pid = info['pid']
                        self._save_pid_to_file(self.launched_pid)
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            # Best-effort only; do not raise
            pass

    def launch_process(self, _exe_path, _exe_args):
        raise NotImplementedError

    def is_process_running(self):
        if self.launched_pid is None:
            return False
        try:
            process = psutil.Process(self.launched_pid)
            if process.is_running():
                return True
            children = process.children(recursive=True)
            return len(children) > 0
        except psutil.NoSuchProcess:
            return False
        except psutil.AccessDenied:
            return False
        except Exception:
            return False

    def terminate_process(self):
        if self.launched_pid is None:
            return False
        try:
            process = psutil.Process(self.launched_pid)
            children = process.children(recursive=True)
            for child in children:
                child.terminate()
            process.terminate()
            try:
                process.wait(timeout=30)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait()
            self._remove_pid_file()
            self.launched_pid = None
            return True
        except psutil.NoSuchProcess:
            self._remove_pid_file()
            self.launched_pid = None
            return False
        except psutil.AccessDenied:
            return False

class WindowsProcessManager(OSProcessManager):
    def pid_file_name(self):
        return 'palworld_server.win.pid'

    def launch_process(self, exe_path, exe_args):
        process = subprocess.Popen(
            [exe_path] + exe_args.split(),
            creationflags=subprocess.HIGH_PRIORITY_CLASS
        )
        self._after_launch(process)

class LinuxProcessManager(OSProcessManager):
    def pid_file_name(self):
        return 'palworld_server.linux.pid'

    def launch_process(self, exe_path, exe_args):
        process = subprocess.Popen([exe_path] + exe_args.split())
        self._after_launch(process)

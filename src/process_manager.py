import subprocess
import psutil
import os

class OSProcessManager:
    def __init__(self):
        self.launched_pid = None
        self._load_pid_from_file()

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
                process.wait(timeout=3)
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

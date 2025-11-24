# Copyright (c) 2024 Nomomo
# Copyright (c) 2024 Kevin Perez - Modified work
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

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

    def set_known_pid(self, pid):
        """Set a known PID and persist it to the PID file."""
        try:
            self.launched_pid = int(pid)
            self._save_pid_to_file(self.launched_pid)
        except Exception:
            # best-effort
            self.launched_pid = None

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

    def find_process_pid(self, name):
        """Find a running process whose attributes contain the given name.

        Returns the PID of the first matching process, or None if not found.
        Matching is case-insensitive and checks process exe path, name, and cmdline.
        """
        try:
            target = (name or "").lower()
            for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cmdline']):
                try:
                    info = proc.info
                    exe = info.get('exe') or ''
                    pname = info.get('name') or ''
                    cmdline_list = info.get('cmdline') or []
                    combined = ' '.join([exe, pname, ' '.join(cmdline_list)]).lower()
                    if target and target in combined:
                        return info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            # best-effort
            pass
        return None

class WindowsProcessManager(OSProcessManager):
    def pid_file_name(self):
        return 'palworld_server.win.pid'

    def launch_process(self, exe_path, exe_args):
        # Detach so the child survives if this controller exits
        creation_flags = (
            subprocess.HIGH_PRIORITY_CLASS
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        process = subprocess.Popen(
            [exe_path] + exe_args.split(),
            creationflags=creation_flags,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        self._after_launch(process)

class LinuxProcessManager(OSProcessManager):
    def pid_file_name(self):
        return 'palworld_server.linux.pid'

    def launch_process(self, exe_path, exe_args):
        # Start a new session (setsid) and detach stdio so it survives parent exit
        process = subprocess.Popen(
            [exe_path] + exe_args.split(),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        self._after_launch(process)

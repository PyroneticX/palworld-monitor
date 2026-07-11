# Copyright (c) 2024 Nomomo
# Copyright (c) 2026 Kevin Perez - Modified work
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
import threading
from src.events import bus, Event


class OSProcessManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.launched_pid = None
        self._load_pid_from_file()
        bus.subscribe(
            Event.CMD_START_SERVER,
            lambda data: self.launch_process(data["exe_path"], data["exe_args"]),
        )
        bus.subscribe(Event.CMD_STOP_SERVER, lambda data: self.terminate_process())

    def pid_file_name(self):
        raise NotImplementedError

    def _after_launch(self, process):
        with self._lock:
            self.launched_pid = process.pid
            self._save_pid_to_file(process.pid)

    def _save_pid_to_file(self, pid):
        try:
            with open(self.pid_file_name(), "w") as f:
                f.write(str(pid))
        except Exception:
            pass

    def _load_pid_from_file(self):
        if os.path.exists(self.pid_file_name()):
            try:
                with open(self.pid_file_name(), "r") as f:
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
        with self._lock:
            try:
                self.launched_pid = int(pid)
                self._save_pid_to_file(self.launched_pid)
            except Exception:
                self.launched_pid = None

    def launch_process(self, _exe_path, _exe_args):
        raise NotImplementedError

    def is_process_running(self):
        with self._lock:
            if self.launched_pid is None:
                return False
            try:
                process = psutil.Process(self.launched_pid)
                if process.is_running():
                    return True
                children = process.children(recursive=True)
                return len(children) > 0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
            except Exception:
                return False

    def terminate_process(self):
        with self._lock:
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
                terminated_pid = self.launched_pid
                self.launched_pid = None
                bus.publish(Event.SERVER_STOPPED, {"pid": terminated_pid})
                return True
            except psutil.NoSuchProcess:
                self._remove_pid_file()
                self.launched_pid = None
                return False
            except psutil.AccessDenied:
                return False
            except Exception:
                return False

    def find_process_pid(self, name):
        try:
            target = (name or "").lower()
            if not target:
                return None
            for proc in psutil.process_iter(attrs=["pid", "name", "exe"]):
                try:
                    info = proc.info
                    exe = (info.get("exe") or "").lower()
                    pname = (info.get("name") or "").lower()
                    # Match against the exe filename and process name only,
                    # not the full command line — substring matches across
                    # args produce false positives (e.g. a test runner whose
                    # -c script contains the search term).
                    if target in exe or target in pname:
                        return info["pid"]
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue
        except Exception:
            pass
        return None

class WindowsProcessManager(OSProcessManager):
    def pid_file_name(self):
        return "palworld_server.win.pid"

    def launch_process(self, exe_path, exe_args):
        process = subprocess.Popen(
            [exe_path] + exe_args.split(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=(
                subprocess.HIGH_PRIORITY_CLASS
                | subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.CREATE_NO_WINDOW
            ),
        )
        self._after_launch(process)
        bus.publish(Event.SERVER_STARTED, {"pid": self.launched_pid})


class LinuxProcessManager(OSProcessManager):
    def pid_file_name(self):
        return "palworld_server.linux.pid"

    def launch_process(self, exe_path, exe_args):
        process = subprocess.Popen(
            [exe_path] + exe_args.split(),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        self._after_launch(process)
        bus.publish(Event.SERVER_STARTED, {"pid": self.launched_pid})




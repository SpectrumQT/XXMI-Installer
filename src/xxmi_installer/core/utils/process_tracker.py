import time
import psutil

from typing import Tuple
from enum import Enum
from multiprocessing import Process, Value

import win32gui
import win32process


def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        #if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

        if found_pid == pid:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


def get_process(process_id=None, process_name=None):
    for process in psutil.process_iter():
        try:
            if process.name() == process_name or process.pid == process_id:
                return process
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


class WaitResult(Enum):
    Found = 0
    NotFound = -100
    Timeout = -200
    Terminated = -300


def wait_for_process(process_name, timeout=10, with_window=False) -> Tuple[WaitResult, int]:
    process = ProcessWaiter(process_name, timeout, with_window)
    process.start()
    process.join()
    result = int(process.data.value)
    """
    Possible returns:
    0...MAX_PID: exit before timeout with process found
    -200: timeout reached
    """

    if result < 0:
        return WaitResult(result), -1
    else:
        return WaitResult.Found, result


def wait_for_process_exit(process_name, timeout=10, kill_timeout=-1) -> Tuple[WaitResult, int]:
    process = ProcessWaiter(process_name, timeout, wait_exit=True, kill_timeout=kill_timeout)
    process.start()
    process.join()
    result = int(process.data.value)
    """
    Possible returns:
    0...MAX_PID: process exit before timeout
    -100: exit before timeout with process not found
    -200: timeout reached with process alive
    -300: process terminated after kill_timeout
    """

    if result < 0:
        return WaitResult(result), -1
    else:
        return WaitResult.Found, result


class ProcessWaiter(Process):
    """
    Waits for process spawn or exit
    Possible self.data.value returns:
    0...MAX_PID: exit before timeout with process found
    -100: exit before timeout with process not found
    -200: timeout reached
    -300: process terminated after kill_timeout
    """
    def __init__(self, process_name, timeout=-1, with_window=False, wait_exit=False, kill_timeout=-1):
        Process.__init__(self)
        self.process_name = process_name
        self.timeout = int(timeout)
        self.with_window = with_window
        self.wait_exit = wait_exit
        self.kill_timeout = kill_timeout
        self.data = Value('i', -100)

    def run(self):

        time_start = time.time()

        while True:

            current_time = time.time()

            if self.timeout != -1 and current_time - time_start >= self.timeout:
                break

            process = get_process(process_name=self.process_name)

            if process is not None:
                # Process is found
                self.data.value = process.pid

                if not self.wait_exit:
                    # We're in wait-for-process-spawn mode
                    if not self.with_window:
                        # Exit loop: process is found and waiting for window is not required
                        return
                    elif len(get_hwnds_for_pid(self.data.value)) != 0:
                        # Exit loop: process is found and window is also found
                        return

                # Start process termination attempts once kill_timeout is reached
                if self.kill_timeout != -1 and current_time - time_start >= self.kill_timeout:
                    self.data.value = -300
                    process.kill()

            elif self.wait_exit:
                return

            time.sleep(0.1)

        # Timeout reached, lets signal it with -200 return code
        self.data.value = -200

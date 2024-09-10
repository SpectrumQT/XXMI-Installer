import argparse
import sys
import tempfile
import logging
import multiprocessing
import traceback
import re
import os
import time

from typing import Union, Callable
from enum import Enum
from dataclasses import dataclass
from threading import Thread, current_thread, main_thread
from queue import Queue, Empty
from pathlib import Path

import core.path_manager as Paths
import core.event_manager as Events

from gui.gui import GUI

from core.asset_managers.launcher_manager import LauncherManager, LauncherManagerConfig
from core.update_manager import UpdateManager, UpdateManagerConfig


class Mode(Enum):
    Install = 'Installer'
    Update = 'Updater'

    def __str__(self):
        return self.value


@dataclass
class ApplicationEvents:

    @dataclass
    class Ready:
        pass

    @dataclass
    class Close:
        delay: int = 0

    @dataclass
    class SettingsUpdate:
        name: str
        value: str

    @dataclass
    class WaitForProcess:
        process_name: str

    @dataclass
    class WaitForProcessExit:
        asset_name: str

    @dataclass
    class Update:
        no_install: bool = False
        force: bool = False
        reinstall: bool = False
        packages: Union[list, None] = None

    @dataclass
    class ShowMessage:
        modal: bool = False
        icon: str = 'messagebox-info-icon.ico'
        title: str = 'Message'
        message: str = '< Text >'
        confirm_text: str = 'OK'
        confirm_command: Union[Callable, None] = None
        cancel_text: str = ''
        cancel_command: Union[Callable, None] = None
        lock_master: bool = True
        screen_center: bool = False

    @dataclass
    class ShowError(ShowMessage):
        icon: str = 'messagebox-error-icon.ico'
        title: str = 'Error'


class Application:
    def __init__(self, gui: GUI):
        self.is_alive = True
        self.gui = gui
        self.instance = self.get_instance()

        parser = argparse.ArgumentParser(description='Installs and updates XXMI Launcher')
        parser.add_argument('-m', '--mode', type=Mode, choices=list(Mode), default=Mode.Install, 
                            help='Switch between "Installer" and "Updater" modes')
        parser.add_argument('-d', '--dist_dir', type=str, default=Path.home() / 'AppData' / 'Roaming' / 'XXMI Launcher',
                            help='Launcher installation directory')
        parser.add_argument('-s', '--shortcut', type=bool, default=True, 
                            help='Default state of "Create Desktop Shortcut" checkbox')
        args = parser.parse_args()

        self.mode = args.mode

        self.launcher_manager = LauncherManager(LauncherManagerConfig(
            installation_dir=str(args.dist_dir),
            create_shortcut=args.shortcut,
            instance=self.instance,
        ))

        self.update_manager = UpdateManager(self, UpdateManagerConfig(), packages=[
            self.launcher_manager.package,
        ])

        self.gui.initialize(self, args.mode)

        self.threads = []
        self.error_queue = Queue()

        Events.Subscribe(Events.Application.Update,
                         lambda event: self.run_as_thread(self.update_manager.update_packages,
                                                          no_install=event.no_install, force=event.force,
                                                          reinstall=event.reinstall, packages=event.packages))
        Events.Subscribe(Events.Application.Close, 
                         lambda event: self.gui.after(event.delay, self.gui.stop))

        if args.mode == Mode.Install:
            Events.Fire(Events.Application.Ready())
        elif args.mode == Mode.Update:
            Events.Fire(Events.Application.Update(force=True, reinstall=True))
            
        self.check_threads()

        self.gui.start()
        
        self.exit()

    def in_updater_mode(self):
        return self.mode == Mode.Update

    def get_instance(self):
        instances = {
            r'.*(WW).*': 'WWMI',
            r'.*(ZZZ).*': 'ZZMI',
            r'.*(HSR).*': 'SRMI',
            r'.*(GI).*': 'GIMI',
        }
        exe_name = Path(sys.executable).name
        for pattern, instance in instances.items():
            if len(re.compile(pattern).findall(exe_name)):
                return instance
        return 'WWMI'

    def run_as_thread(self, callback, *args, **kwargs):
        def wrap_errors(func, *func_args, **func_kwargs):
            try:
                func(*func_args, **func_kwargs)
            except Exception as e:
                self.error_queue.put_nowait((e, traceback.format_exc()))
        thread = Thread(target=wrap_errors, args=(callback, *args), kwargs=kwargs)
        self.threads.append(thread)
        thread.start()

    def check_threads(self):
        self.gui.after(50, self.check_threads)
        # Remove finished threads from the list
        self.threads = [thread for thread in self.threads if thread.is_alive()]
        # Raise exceptions sent to error queue by threads
        try:
            if self.gui.state() != 'normal':
                return
            self.report_thread_error()
            # raise exception
        except Empty:
            pass

    def report_thread_error(self):
        (error, trace) = self.error_queue.get_nowait()
        logging.error(trace)
        gui_open = self.gui.state() == 'normal'
        self.gui.show_messagebox(Events.Application.ShowError(
            modal=True,
            screen_center=not gui_open,
            lock_master=gui_open,
            message=str(error),
        ))
        if gui_open:
            self.gui.after(100, Events.Fire, Events.Application.Ready())

    def watchdog(self, timeout: int = 15):
        timeout = time.time() + timeout
        while True:
            time.sleep(0.1)
            if not self.is_alive:
                return
            if time.time() > timeout:
                break
        logging.error('[WATCHDOG]: Shutting down stuck process...')
        os._exit(os.EX_OK)

    def exit(self):
        try:
            assert current_thread() is main_thread()
        except Exception as e:
            self.error_queue.put_nowait((e, traceback.format_exc()))
        # Start watchdog to forcefully shutdown process in 15 seconds
        watchdog_thread = Thread(target=self.watchdog, kwargs={'timeout': 15})
        watchdog_thread.start()
        # Join active threads
        logging.debug(f'Joining threads...')
        for thread in self.threads:
            thread.join()
        # Join watchdog thread
        logging.debug(f'Joining watchdog thread...')
        self.is_alive = False
        watchdog_thread.join()
        # Report any errors left in queue
        while True:
            try:
                self.report_thread_error()
            except Empty:
                break
        logging.debug(f'App Exit')
        

if __name__ == '__main__':
    multiprocessing.freeze_support()

    try:
        root_path = Path(sys._MEIPASS).resolve()
        log_name = Path(sys.executable).stem
    except Exception:
        root_path = Path().resolve()
        log_name = root_path.name

    Paths.initialize(root_path)

    logging.basicConfig(filename=Path(tempfile.gettempdir()) / f'{log_name}-Log.txt',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        level=logging.DEBUG)

    logging.debug(f'App Start')

    gui = GUI()

    try:
        Application(gui)
    except Exception as e:
        logging.exception(e)
        gui.show_messagebox(Events.Application.ShowError(
            modal=True,
            screen_center=True,
            lock_master=False,
            message=str(e),
        ))

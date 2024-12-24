import sys
import logging
import multiprocessing

from pathlib import Path


if __name__ == '__main__':
    # Multiprocessing support for Pyinstaller
    multiprocessing.freeze_support()

    try:
        # Pyinstaller (release build)
        root_path = Path(sys._MEIPASS).resolve()
        log_name = Path(sys.executable).stem
    except Exception:
        # Python (native)
        root_path = Path().resolve()
        log_name = root_path.name

    logging.basicConfig(filename=Path(sys.executable).parent / f'{log_name}-Log.txt',
                        encoding='utf-8',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        level=logging.DEBUG)

    logging.debug(f'App Start')

    try:
        import core.path_manager as Paths
        Paths.initialize(root_path)

        from gui.windows.main.main_window import MainWindow
        gui = MainWindow()

        import core.event_manager as Events

        from core.application import Application
        Application(gui)

    except Exception as e:
        logging.exception(e)

        gui.show_messagebox(Events.Application.ShowError(
            modal=True,
            screen_center=True,
            lock_master=False,
            message=str(e),
        ))

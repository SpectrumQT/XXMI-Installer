import logging
import pyglet

import core.path_manager as Paths
import core.event_manager as Events
import core.config_manager as Config

from customtkinter import set_appearance_mode, set_default_color_theme

from gui.windows.message_window import MessageWindow

from gui.classes.windows import UIMainWindow, limit_scaling

from gui.events import Stage
from gui.windows.main.installer_frame.installer_frame import InstallerFrame
from gui.windows.main.custom_install_frame.custom_install_frame import CustomInstallFrame
from gui.windows.main.error_frame.error_frame import ErrorFrame

log = logging.getLogger(__name__)

# from customtkinter import set_widget_scaling, set_window_scaling, deactivate_automatic_dpi_awareness
# set_widget_scaling(2)
# set_window_scaling(2)
# deactivate_automatic_dpi_awareness()
# Limit automatic scaling in a way to fit arbitrary width and height on screen
limit_scaling(1280, 720)


class MainWindow(UIMainWindow):
    def __init__(self):
        super().__init__()
        self.hide()

        # Set appearance mode to same as one of user OS
        set_appearance_mode('System')
        # Fix pyglet font load
        pyglet.options['win32_gdi_font'] = True

        # Load custom tkinter theme
        try:
            set_default_color_theme(str(Paths.App.Themes / 'Default' / 'custom-tkinter-theme.json'))
        except Exception as e:
            log.exception(e)

        # Load custom fonts
        try:
            pyglet.font.add_file(str(Paths.App.Themes / 'Default' / 'Fonts' / 'Asap.ttf'))
        except Exception as e:
            log.exception(e)

    def initialize(self):
        Events.Subscribe(Events.Application.ShowMessage,
                         lambda event: self.show_messagebox(event))
        Events.Subscribe(Events.Application.ShowError,
                         lambda event: self.show_messagebox(event))
        Events.Subscribe(Events.Application.ShowWarning,
                         lambda event: self.show_messagebox(event))
        Events.Subscribe(Events.Application.ShowInfo,
                         lambda event: self.show_messagebox(event))

        import gui.vars as Vars

        Vars.Settings.initialize(Config.Config, self)
        Vars.Settings.load()

        self.cfg.title = 'XXMI Installer'
        self.cfg.icon_path = Paths.App.Themes / 'Default' / 'window-icon.ico'

        self.cfg.width = 854
        self.cfg.height = 480

        self.apply_config()

        self.center_window()

        self.installer_frame = self.put(InstallerFrame(self))
        self.installer_frame.grid(row=0, column=0, padx=0, pady=0, sticky='news')

        self.custom_install_frame = self.put(CustomInstallFrame(self, self.installer_frame.canvas))
        # self.custom_install_frame.grid(row=0, column=0, padx=10, pady=10, sticky='news')

        Events.Subscribe(Events.Application.MoveWindow, lambda event: self.move(event.offset_x, event.offset_y))

        # Events.Fire(Events.Application.StatusUpdate(status='Some radical actions ongoing...'))
        # Events.Fire(Events.PackageManager.UpdateDownloadProgress(downloaded_bytes=1000, total_bytes=10000))

        # Events.Fire(Events.Application.Busy())
        # Events.Fire(Events.PackageManager.InitializeDownload())
        # Events.Fire(Events.PackageManager.InitializeInstallation())

        self.show()

        Events.Subscribe(Events.Application.Minimize,
                         lambda event: self.minimize())
        Events.Subscribe(Events.Application.Close, self.handle_close)

    def handle_close(self, event):
        self.after(event.delay, self.close)

    def close(self):
        Events.Fire(Events.Application.Ready())
        super().close()

    def show_messagebox(self, event):
        if not self.exists:
            return False

        if self.cfg.title == 'UIWindow':
            messagebox = MessageWindow(self, icon=event.icon,
                                    title=event.title, message=event.message,
                                    confirm_text=event.confirm_text, confirm_command=event.confirm_command,
                                    cancel_text=event.cancel_text, cancel_command=event.cancel_command,
                                    lock_master=event.lock_master, screen_center=event.screen_center)

            if event.modal:
                self.wait_window(messagebox)

            return messagebox.response

        else:
            messagebox = self.put(ErrorFrame(self, icon=event.icon, canvas=self.installer_frame.canvas,
                                    title=event.title, message=event.message,
                                    confirm_text=event.confirm_text, confirm_command=event.confirm_command,
                                    cancel_text=event.cancel_text, cancel_command=event.cancel_command))
            if event.modal:
                self.wait_variable(messagebox.wait_var)

            return messagebox.response

    def report_callback_exception(self, exc, val, tb):
        # raise exc
        custom_install = not self.custom_install_frame.is_hidden
        Events.Fire(Events.Application.Ready())
        self.show_messagebox(Events.Application.ShowError(
            modal=True,
            message=val,
        ))
        logging.exception(val)
        if custom_install:
            Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.CustomInstall))

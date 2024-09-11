import logging
import customtkinter

import core.path_manager as Paths
import core.event_manager as Events

import gui.vars as gui_vars
from gui.windows.messagebox import Messagebox
from gui.enums import Stage
from gui.frames.installation_config import InstallationConfig
from gui.frames.download_status import DownloadStatus
from gui.frames.installation_status import InstallationStatus


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.theme_path = Paths.App.Resources

    def initialize(self, app, display_mode):
        self.app = app

        self.display_mode = display_mode

        self.setup_window()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_frame = None
        self.installation_config_frame = InstallationConfig(self, app)
        self.download_status_frame = DownloadStatus(self)
        self.installation_status_frame = InstallationStatus(self)

        Events.Subscribe(Events.Application.ShowMessage,
                         lambda event: self.show_messagebox(event))
        Events.Subscribe(Events.Application.ShowError,
                         lambda event: self.show_messagebox(event))

        Events.Subscribe(Events.Application.Ready,
                         lambda event: self.set_stage(Stage.Configuration))
        Events.Subscribe(Events.UpdateManager.InitializeDownload,
                         lambda event: self.set_stage(Stage.Download))
        Events.Subscribe(Events.UpdateManager.InitializeInstallation,
                         lambda event: self.set_stage(Stage.Installation))

    def setup_window(self):
        if self.app.in_updater_mode():
            self.title("XXMI Launcher Updater")
        else:
            self.title("XXMI Launcher Installer")

        self.iconbitmap(self.theme_path / 'title-bar-icon.ico', self.theme_path / 'title-bar-icon.ico')

        customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
        customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

        self.resizable(False, False)

    def position_window(self, window_width, window_height):
        x = int(((self.winfo_screenwidth() / 2) - (window_width / 2)) * self._get_window_scaling())
        y = int(((self.winfo_screenheight() / 2) - (window_height / 1.5)) * self._get_window_scaling())
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def set_stage(self, stage):
        if self.current_frame is not None:
            self.current_frame.grid_forget()

        if stage == Stage.Configuration:
            self.current_frame = self.installation_config_frame
            self.position_window(640, 230)
        elif stage == Stage.Download:
            self.current_frame = self.download_status_frame
            self.position_window(640, 164)
        elif stage == Stage.Installation:
            self.current_frame = self.installation_status_frame
            self.position_window(640, 164)

        self.current_frame.grid(row=0, column=0, padx=0, pady=0, sticky="news")

    def show_messagebox(self, event):
        messagebox = Messagebox(self, icon=event.icon, title=event.title, message=event.message,
                                confirm_text=event.confirm_text, confirm_command=event.confirm_command,
                                cancel_text=event.cancel_text, cancel_command=event.cancel_command,
                                lock_master=event.lock_master, screen_center=event.screen_center)
        if event.modal:
            self.wait_window(messagebox)

        return messagebox.response

    def start(self):
        gui_vars.announce()
        self.mainloop()

    def stop(self):
        self.destroy()

    def report_callback_exception(self, exc, val, tb):
        self.show_messagebox(Events.Application.ShowError(
            modal=True,
            message=val,
        ))
        Events.Fire(Events.Application.Ready())
        logging.exception(val)
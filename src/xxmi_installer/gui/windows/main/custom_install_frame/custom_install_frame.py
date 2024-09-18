from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, Tuple, List, Optional, Any
from pathlib import Path

from customtkinter import ThemeManager
from customtkinter import DrawEngine, CTkFrame, CTkBaseClass
from customtkinter import filedialog, CTkEntry, END

import core.event_manager as Events
import core.path_manager as Paths
import core.config_manager as Config
import gui.vars as Vars

from gui.events import Stage
from gui.classes.containers import UIFrame
from gui.classes.widgets import UIButton, UIText, UICheckbox, UILabel, UIImageButton, UIEntry


class CustomInstallFrame(UIFrame):
    def __init__(self, master, canvas, **kwargs):
        super().__init__(master=master, canvas=canvas, width=580, height=200, fg_color='#26262f', corner_radius=0, **kwargs)


        self.set_background_image(image_path='background-image.png', width=master.cfg.width,
                                  height=master.cfg.height, x=0, y=0, anchor='nw', brightness=1.0, opacity=1)

        self.put(CloseButton(self))

        self.put(InstallationFolderLabel(self)).place(x=0, y=0)
        self.put(InstallationFolderEntry(self)).place(x=0, y=45)
        self.put(ChangeInstallationFolderButton(self)).place(x=485, y=45)
        self.put(CreateShortcutCheckbox(self)).place(x=0, y=110)
        self.put(InstallButton(self)).place(x=395, y=140)

        self.hide()

        self.subscribe_show(Events.GUI.InstallerFrame.StageUpdate, lambda event: event.stage == Stage.CustomInstall)

    def _hide(self):
        self.place_forget()
        super()._hide()
        
    def _show(self):
        Vars.Settings.initialize_vars()
        Vars.Settings.load()
        self.place(x=137, y=154)
        super()._show()


class CloseButton(UIImageButton):
    def __init__(self, master):
        super().__init__(
            x=716,
            y=142,
            width=18,
            height=18,
            button_image_path='button-system-close.png',
            button_normal_opacity=0.8,
            button_hover_opacity=1,
            button_selected_opacity=1,
            bg_image_path='button-system-background.png',
            bg_width=24,
            bg_height=24,
            bg_normal_opacity=0,
            bg_hover_opacity=0.1,
            bg_selected_opacity=0.2,
            command=self.close,
            master=master)
        self.set_tooltip(f'Close', delay=0.1)

    def close(self):
        self.master.hide()
        Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.Ready))


class InstallationFolderLabel(UILabel):
    def __init__(self, master):
        super().__init__(
            text='Installation Folder',
            font=('Microsoft YaHei', 18, 'bold'),
            fg_color='transparent',
            text_color='white',
            master=master)


class InstallationFolderEntry(UIEntry):
    def __init__(self, master):
        super().__init__(
            textvariable=Vars.Launcher.installation_dir,
            width=490,
            height=42,
            font=('Arial', 16),
            text_color='#dddddd',
            fg_color='#323241',
            border_width=0,
            corner_radius=8,
            master=master)
        # self.trace_write(Vars.Active.Migoto.unsafe_mode, self.handle_unsafe_mode_update)
        self.set_tooltip('Folder where XXMI Launcher.exe and XXMI per-game instance folders will be located.')


class ChangeInstallationFolderButton(UIButton):
    def __init__(self, master):
        super().__init__(
            text='Browse...',
            command=self.change_installation_folder,
            width=90,
            height=42,
            font=('Asap', 15),
            fg_color='#323241',
            hover_color='#323241',
            text_color='#dddddd',
            text_color_hovered='#ffffff',
            border_width=0,
            corner_radius=8,
            background_corner_colors=('#323241','#26262f','#26262f','#323241'),
            master=master)

    def change_installation_folder(self, event=None):
        installation_folder = filedialog.askdirectory(initialdir=Vars.Launcher.installation_dir.get())
        if installation_folder == '':
            return
        Events.Fire(Events.LauncherManager.AssertInstallationFolder(installation_folder=installation_folder))
        installation_path = Path(installation_folder)
        if installation_path.name != 'XXMI Launcher':
            if next(installation_path.iterdir(), None):
                installation_path /= 'XXMI Launcher'
        Vars.Launcher.installation_dir.set(str(installation_path))


class CreateShortcutCheckbox(UICheckbox):
    def __init__(self, master):
        super().__init__(
            text='Create Desktop Shortcut',
            variable=Vars.Launcher.create_shortcut,
            checkbox_width=20,
            checkbox_height=20,
            text_color='#dddddd',
            text_color_hovered='#ffffff',
            hover_color='#ffffff',
            master=master)
        self.set_tooltip('Make shortcut to XXMI Launcher.exe on desktop.')


class InstallButton(UIButton):
    def __init__(self, master):
        super().__init__(
            text='Install',
            command=self.install,
            width=180,
            height=38,
            font=('Microsoft YaHei', 16, 'bold'),
            fg_color='#eeeeee',
            text_color='#000000',
            hover_color='#ffffff',
            border_width=0,
            corner_radius=8,
            master=master)

    def install(self):
        Events.Fire(Events.LauncherManager.AssertInstallationFolder(installation_folder=Vars.Launcher.installation_dir.get()))
        Vars.Settings.save()
        Events.Fire(Events.Application.InstallLauncher())





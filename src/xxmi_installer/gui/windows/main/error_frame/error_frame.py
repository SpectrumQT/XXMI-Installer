from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, Tuple, List, Optional, Any
from pathlib import Path

from customtkinter import ThemeManager
from customtkinter import DrawEngine, CTkFrame, BooleanVar
from customtkinter import filedialog, CTkEntry, END

import core.event_manager as Events
import core.path_manager as Paths
import core.config_manager as Config
import gui.vars as Vars

from gui.events import Stage
from gui.classes.containers import UIFrame
from gui.classes.widgets import UIImage, UIText, UICheckbox, UILabel, UIImageButton, UIEntry
from gui.windows.message_window import MessageFrame


class ErrorFrame(UIFrame):
    def __init__(self, master, canvas=None, icon='info-icon.ico', title='Message', message='< Text >',
                 confirm_text='OK', confirm_command=None, cancel_text='', cancel_command=None, **kwargs):
        super().__init__(master=master, canvas=canvas, width=420, height=150, fg_color='#26262f', corner_radius=0,
                         **kwargs)

        self.response = None
        self.wait_var = BooleanVar(master=self, value=False)

        self.message_frame = MessageFrame(master, data_handler=self, message=message, width=400, height=150,
                              confirm_text=confirm_text, confirm_command=confirm_command,
                              cancel_text=cancel_text, cancel_command=cancel_command)
        self.message_frame.place(x=217, y=180)
        self.message_frame.hide()

        self.set_background_image(image_path='background-image.png', width=master.cfg.width,
                                  height=master.cfg.height, x=0, y=0, anchor='nw', brightness=1.0, opacity=1)

        self.put(IconImage(self, image_path=icon))
        self.put(TitleText(self, title=title))
        self.put(CloseButton(self))

        self.hide()

        self.after(50, self.show)
        self.after(50, self.message_frame.show)

    def close(self):
        self.background_image.destroy()
        self.message_frame.destroy()
        self.destroy()
        self.wait_var.set(True)


class IconImage(UIImage):
    def __init__(self, master, image_path):
        super().__init__(master=master,
                         image_path=f'messagebox-{image_path}',
                         width=24,
                         height=24,
                         x=226,
                         y=168,)


class TitleText(UIText):
    def __init__(self, master, title):
        super().__init__(
            text=title,
            font=('Microsoft YaHei', 14, 'bold'),
            fill='white',
            activefill='white',
            x=265,
            y=168,
            master=master)


class CloseButton(UIImageButton):
    def __init__(self, master):
        super().__init__(
            x=625,
            y=168,
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
        self.master.close()

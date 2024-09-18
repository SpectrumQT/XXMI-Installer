import logging

import core.path_manager as Paths
import core.config_manager as Config

from gui.classes.windows import UIToplevel
from gui.classes.containers import UIFrame, UIScrollableFrame
from gui.classes.widgets import UILabel, UIButton

log = logging.getLogger(__name__)


class MessageWindow(UIToplevel):
    def __init__(self, master, icon='info-icon.ico', title='Message', message='< Text >',
                 confirm_text='OK', confirm_command=None, cancel_text='', cancel_command=None,
                 lock_master=True, screen_center=False):
        super().__init__(master, lock_master=lock_master, fg_color='#26262f')

        self.response = None

        self.title(title)

        self.cfg.title = title

        self.cfg.icon_path = Paths.App.Themes / 'Default' / 'MessageWindow' / icon

        self.cfg.width = 600
        self.cfg.height = 225

        self.apply_config()

        message_frame = MessageFrame(self, message=message, width=self.cfg.width, height=self.cfg.height,
                              confirm_text=confirm_text, confirm_command=confirm_command,
                              cancel_text=cancel_text, cancel_command=cancel_command)

        self.put(message_frame).pack(side='top', fill='both', expand=True)

        self.center_window(anchor_to_master=not screen_center)

        self.update()
        message_frame.show()

        self.after(50, self.open)

    def close(self):
        log.debug('Messagebox window closed')
        super().close()


class MessageFrame(UIFrame):
    def __init__(self, master, width, height, message='< Text >', confirm_text='OK', confirm_command=None, cancel_text='', cancel_command=None, data_handler=None):
        super().__init__(master, width=width, height=height, fg_color='#26262f', corner_radius=0)

        self.data_handler = data_handler or master

        class MessageScrollableFrame(UIScrollableFrame):
            def __init__(self, master):
                super().__init__(
                    width=width,
                    height=height-70,
                    corner_radius=0,
                    fg_color='#26262f',
                    hide_scrollbar=True,
                    master=master)

                self.put(MessageTextLabel(self, str(message).strip(), width=width, height=height)).pack(pady=(0, 0))

                self.update()

        self.put(MessageScrollableFrame(self)).pack(padx=10, pady=(10, 15))

        if confirm_text:
            self.put(ConfirmButton(self, confirm_text, confirm_command)).pack(padx=(60, 60), pady=(0, 15), side='right' if cancel_text else 'bottom')

        if cancel_text:
            self.put(CancelButton(self, cancel_text, cancel_command)).pack(padx=(60, 60), pady=(0, 15), side='left')

        self.hide()
        # self.show()


class MessageTextLabel(UILabel):
    def __init__(self, master, message, width, height):
        super().__init__(
            text=message,
            wraplength=width,
            height=height-70,
            justify='center',
            anchor='center',
            font=('Asap', 16),
            text_color='#dddddd',
            master=master)


class ConfirmButton(UIButton):
    def __init__(self, master, confirm_text, confirm_command):
        super().__init__(
            text=confirm_text,
            command=lambda: self.confirm(confirm_command),
            fg_color='#eeeeee',
            text_color='#000000',
            hover_color='#ffffff',
            width=150,
            height=28,
            corner_radius=8,
            master=master)

    def confirm(self, confirm_command):
        if confirm_command is not None:
            confirm_command()
        self.master.data_handler.response = True
        self.master.data_handler.close()


class CancelButton(UIButton):
    def __init__(self, master, cancel_text, cancel_command):
        super().__init__(
            text=cancel_text,
            command=lambda: self.cancel(cancel_command),
            fg_color='#e5e5e5',
            width=150,
            height=28,
            corner_radius=8,
            master=master)

    def cancel(self, cancel_command):
        if cancel_command is not None:
            cancel_command()
        self.master.data_handler.response = False
        self.master.data_handler.close()

import customtkinter
from customtkinter import CTkToplevel
from customtkinter import CTkLabel, CTkButton


class Messagebox(CTkToplevel):
    def __init__(self, master, icon='messagebox-info-icon.ico', title='Message', message='< Text >',
                 confirm_text='OK', confirm_command=None, cancel_text='', cancel_command=None,
                 lock_master=True, screen_center=False):
        super().__init__(master)

        self.lock_master = lock_master
        self.response = None

        self.title(title)

        self.after(200, lambda: self.iconbitmap(self.master.theme_path / icon))

        self.setup_window()

        self.position_window(480, 150, screen_center)

        self.message_label = CTkLabel(self, text=message, wraplength=440, justify='center')
        self.message_label.pack(pady=(20, 20), fill='y', expand=True)

        if confirm_text:
            self.confirm_button = CTkButton(self, text=confirm_text, command=lambda: self.confirm(confirm_command), fg_color='#666666', text_color='#ffffff', hover_color='#888888')
            self.confirm_button.pack(padx=(50, 50), pady=(0, 15), side='right' if cancel_text else 'bottom')

        if cancel_text:
            self.cancel_button = CTkButton(self, text=cancel_text, command=lambda: self.cancel(cancel_command), fg_color='#d5d5d5')
            self.cancel_button.pack(padx=(50, 50), pady=(0, 15), side='left')

        self.protocol('WM_DELETE_WINDOW', self.close)

        if self.lock_master:
            self.grab_set()
            self.master.attributes('-disabled', 1)

    def setup_window(self):
        # customtkinter.set_default_color_theme(self.master.theme_path / 'custom-tkinter-theme.json')
        self.resizable(False, False)

    def position_window(self, window_width, window_height, relative_to_screen=False):
        self.update_idletasks()
        if not relative_to_screen:
            x = int(self.master.winfo_rootx() + self.master.winfo_width() / 2 - window_width / 2)
            y = int(self.master.winfo_rooty() + self.master.winfo_height() / 2 - window_height / 2 - 16*2)
        else:
            x = int(self.winfo_screenwidth() / 2 - window_width / 2)
            y = int(self.winfo_screenheight() / 2 - window_height / 2 - 16*2)
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def confirm(self, confirm_command):
        if confirm_command is not None:
            confirm_command()
        self.response = True
        self.close()

    def cancel(self, cancel_command):
        if cancel_command is not None:
            cancel_command()
        self.response = False
        self.close()

    def close(self):
        if self.lock_master:
            self.master.attributes('-disabled', 0)
            self.grab_release()
        self.destroy()



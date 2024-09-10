import customtkinter
from customtkinter import filedialog, CTkEntry, END
from tkinter import INSERT, Menu

from pathlib import Path

import core.path_manager as Paths
import core.event_manager as Events

import gui.vars as gui_vars
from gui.windows.tooltip import ToolTip


class InstallationConfig(customtkinter.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")

        self.app = app

        self.grid_columnconfigure(0, weight=1)

        self.install_path_label = customtkinter.CTkLabel(self, text="Select Installation Folder", fg_color="transparent",
                                                         font=("Roboto", 16, 'bold'))
        self.install_path_label.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w", columnspan=2)

        installation_dir = gui_vars.new(self, self.app.launcher_manager.cfg, 'installation_dir')
        self.install_path_entry = UIEntry(self, height=36, font=("Arial", 14), textvariable=installation_dir)
        self.install_path_entry.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        ToolTip(self.install_path_entry, "Folder where XXMI Launcher.exe and XXMI per-game instance folders will be located.")
        self.install_path_entry.bind("<<Paste>>", self.paste_to_selection)

        self.install_path_button = customtkinter.CTkButton(self, text="Change", command=self.open_install_path_dialog,
                                                           height=36, width=80, font=("Roboto", 14))
        self.install_path_button.grid(row=1, column=1, padx=(0, 20), pady=(0, 20))
        ToolTip(self.install_path_button, "Open Installation Folder Selection Dialogue.")

        create_shortcut = gui_vars.new(self, self.app.launcher_manager.cfg, 'create_shortcut')
        self.create_shortcut_checkbox = customtkinter.CTkCheckBox(self, text="Create Desktop Shortcut", variable=create_shortcut)
        self.create_shortcut_checkbox.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
        ToolTip(self.create_shortcut_checkbox, "Make shortcut to XXMI Launcher.exe on desktop.")

        self.start_install_button = customtkinter.CTkButton(self, text="Download & Install",
                                                            command=self.download_and_install,
                                                            font=("Roboto", 14, 'bold'), width=220, height=34)
        self.start_install_button.grid(row=3, column=0, padx=20, pady=(0, 20), columnspan=2)

    def paste_to_selection(self, event):
        try:
            event.widget.delete('sel.first', 'sel.last')
        except:
            pass
        event.widget.insert('insert', event.widget.clipboard_get())
        return 'break'

    def download_and_install(self):
        gui_vars.save()

        installation_path = Path(self.install_path_entry.get())

        if 'Wuthering Waves Game' in str(installation_path):
            raise ValueError(f"Installation folder must be located outside of Wuthering Waves game folder!")

        for filename in ['KRInstallExternal.exe', 'Wuthering Waves.exe', 'Client-Win64-Shipping.exe']:
            if Path(installation_path / filename).exists():
                raise ValueError(f"Installation folder must be located outside of Wuthering Waves game folder!")

        Paths.verify_path(installation_path)
        Paths.App.Downloads = installation_path

        Events.Fire(Events.Application.Update(force=True, reinstall=True))

    def open_install_path_dialog(self):
        install_path = filedialog.askdirectory(initialdir=self.install_path_entry.get())
        if install_path == '':
            return
        install_path = Path(install_path)
        if install_path.name != 'XXMI Launcher':
            if next(install_path.iterdir(), None):
                install_path /= 'XXMI Launcher'
        self.set_install_path(install_path)

    def set_install_path(self, install_path):
        self.install_path_entry.delete(0, customtkinter.END)
        self.install_path_entry.insert(0, install_path)

    def set_create_shortcut(self, create_shortcut):
        if create_shortcut:
            self.create_shortcut_checkbox.select()
        else:
            self.create_shortcut_checkbox.deselect()


class UIEntry(CTkEntry):
    def __init__(self,
                 master,
                 **kwargs):
        CTkEntry.__init__(self, master, **kwargs)

        self.state_log = [('', 0)]
        self.state_id = -1

        self.bind("<Key>", self.initialize_state_log)
        self.bind("<KeyRelease>", self.add_state)
        self.bind("<<Cut>>", lambda event: self.after(200, self.add_state))
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<Button-3>", self.handle_button3)
        self.bind("<<Paste>>", self.paste_to_selection)

        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut")
        self.context_menu.add_command(label="Copy")
        self.context_menu.add_command(label="Paste")

    def event_generate(self, *args, **kwargs):
        self._entry.event_generate(*args, **kwargs)

    # def destroy(self):
    #     # Remove default write-trace callback for textvariable if exists
    #     if not (self._textvariable is None or self._textvariable == ""):
    #         self._textvariable.trace_vdelete('w', self._textvariable_callback_name)
    #     super().destroy()

    def set(self, value):
        self.delete(0, END)
        self.insert(0, value)

    def handle_button3(self, event=None):
        self.initialize_state_log()
        self.show_context_menu(event)

    def initialize_state_log(self, event=None):
        if len(self.state_log) == 1:
            self.state_log[0] = (self.get(), self.index(INSERT))
            self.state_id = 0
            # print(f'INIT STATE: {self.state_log}')
        else:
            self.set_state(self.state_id, None, self.index(INSERT))

    def get_state(self, state_id: int = None):
        if state_id is None:
            state_id = self.state_id
        return self.state_log[state_id][0]

    def get_index_after_state(self, state_id: int = None):
        if state_id is None:
            state_id = self.state_id
        return self.state_log[state_id][1]

    def set_state(self, state_id, value=None, index=None):
        if state_id < len(self.state_log):
            state = self.state_log[state_id]
            self.state_log[state_id] = (value or state[0], index or state[1])
        else:
            self.state_log.append((value, index))

    def add_state(self, event=None):
        if len(self.state_log) > 0:
            if self.get() == self.get_state():
                # print(f'NO CHANGES: {self.state_log}')
                return

            old_states = self.state_log[self.state_id:]
            # print(f'REMOVE: {old_states}  STATES: {self.state_log}')
            self.state_log = self.state_log[:self.state_id+1]

        self.state_id = len(self.state_log)
        self.set_state(self.state_id, self.get(), self.index(INSERT))
        # print(f'ADD State {self.state_id} ({self.get_state()}) STATES: {self.state_log}')

    def paste_to_selection(self, event):
        self.initialize_state_log()
        try:
            event.widget.delete('sel.first', 'sel.last')
        except:
            pass
        event.widget.insert('insert', event.widget.clipboard_get())
        self.add_state()
        return 'break'

    def undo(self, event=None):
        new_state_id = self.state_id - 1
        # print(f'UNDO: State {self.state_id} -> {new_state_id} / {len(self.state_log)} ({self.get_state()} -> {self.get_state(new_state_id)})')
        if new_state_id >= 0:
            # print(f'SET: {self.get_state(new_state_id)} INDEX {self.get_index_after_state(new_state_id)}')
            self.set(self.get_state(new_state_id))
            self.icursor(self.get_index_after_state(new_state_id))
            self.state_id = new_state_id

    def redo(self, event=None):
        new_state_id = self.state_id + 1
        # print(f'REDO: State {self.state_id} -> {new_state_id} / {len(self.state_log)} ({self.get_state()})')
        if new_state_id < len(self.state_log):
            # print(f'SET: {self.get_state(new_state_id)} INDEX {self.get_index_after_state(new_state_id)}')
            self.set(self.get_state(new_state_id))
            self.icursor(self.get_index_after_state(new_state_id))
            self.state_id = new_state_id

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu.entryconfigure('Cut', command=lambda: self.event_generate('<<Cut>>'))
        self.context_menu.entryconfigure('Copy', command=lambda: self.event_generate('<<Copy>>'))
        self.context_menu.entryconfigure('Paste', command=lambda: self.event_generate('<<Paste>>'))
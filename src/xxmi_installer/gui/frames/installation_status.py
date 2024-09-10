import customtkinter

import core.event_manager as Events


class InstallationStatus(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        self.title_label = customtkinter.CTkLabel(self, text="Installation In Progress", fg_color="transparent",
                                                         font=("Roboto", 16, 'bold'))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w", columnspan=2)
        if self.master.app.in_updater_mode():
            self.title_label.configure(text="Update In Progress")

        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", height=32, mode="indeterminate")
        self.progress_bar.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew", columnspan=2)
        self.progress_bar.start()

        self.status_label = customtkinter.CTkLabel(self, text="", fg_color="transparent",
                                                         font=("Roboto", 14))
        self.status_label.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")

        Events.Subscribe(Events.Application.WaitForProcessExit,
                         lambda event: self.update_status(f'Waiting for {event.asset_name} to close...'))

        Events.Subscribe(Events.UpdateManager.StartIntegrityVerification,
                         lambda event: self.update_status(f'Verifying {event.asset_name} integrity...'))
        Events.Subscribe(Events.UpdateManager.StartFileWrite,
                         lambda event: self.update_status(f'Writing {event.asset_name}...'))
        Events.Subscribe(Events.UpdateManager.StartUnpack,
                         lambda event: self.update_status(f'Unpacking {event.asset_name}...'))

        Events.Subscribe(Events.LauncherManager.StartCreateShortcuts,
                         lambda event: self.update_status(f'Creating desktop shortcut...'))
        Events.Subscribe(Events.LauncherManager.StartLauncher,
                         lambda event: self.update_status(f'Starting {event.asset_name}...'))

    def update_status(self, status_text):
        self.status_label.configure(text=status_text)

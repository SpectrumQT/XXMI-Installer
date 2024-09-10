import customtkinter

import core.event_manager as Events


class DownloadStatus(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.grid_columnconfigure(0, weight=100)
        self.grid_columnconfigure(1, weight=1)

        self.title_label = customtkinter.CTkLabel(self, text="Download In Progress", fg_color="transparent",
                                                         font=("Roboto", 16, 'bold'))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w", columnspan=2)

        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", height=32, width=600)
        self.progress_bar.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew", columnspan=2)

        self.status_label = customtkinter.CTkLabel(self, text="Connecting to GitHub... ", fg_color="transparent",
                                                         font=("Roboto", 14))
        self.status_label.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")

        self.progress_label = customtkinter.CTkLabel(self, text="", fg_color="transparent", font=("Roboto", 14))
        self.progress_label.grid(row=2, column=1, padx=20, pady=(0, 20), sticky="e")

        Events.Subscribe(Events.UpdateManager.StartDownload,
                         lambda event: self.initialize_progress(event.asset_name))
        Events.Subscribe(Events.UpdateManager.UpdateDownloadProgress,
                         lambda event: self.update_progress(event.downloaded_bytes, event.total_bytes))

        self.initialize_download()

    def update_status(self, status_text):
        self.status_label.configure(text=status_text)

    def initialize_download(self):
        self.update_status(f'Connecting to GitHub...')
        self.progress_label.configure(text='')
        self.progress_bar.set(100)
        self.progress_bar.set(0)

    def initialize_progress(self, asset_file_name):
        self.progress_bar.set(0)
        self.progress_label.configure(text='Initializing download...')
        self.update_status(asset_file_name)

    def update_progress(self, downloaded_bytes, total_bytes):
        progress = downloaded_bytes / total_bytes
        progress_text = '%.2f%% (%s/%s)' % (progress * 100, self.format_size(downloaded_bytes), self.format_size(total_bytes))
        self.progress_label.configure(text=progress_text)
        self.progress_bar.set(progress)

    @staticmethod
    def format_size(num_bytes):
        units = ('B', 'KB', 'MB', 'GB', 'TB')
        for power, unit in enumerate(units):
            if num_bytes < 1024 ** (power + 1):
                return '%.2f%s' % (num_bytes / 1024 ** power, unit)

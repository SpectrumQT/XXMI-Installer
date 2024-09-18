import core.event_manager as Events
import core.path_manager as Paths
import core.config_manager as Config
import gui.vars as Vars

from gui.events import Stage
from gui.classes.containers import UIFrame
from gui.classes.widgets import UIButton, UIText, UIProgressBar, UILabel, UIImageButton, UIImage
from gui.windows.main.installer_frame.top_bar import TopBarFrame
from gui.windows.main.installer_frame.bottom_bar import BottomBarFrame


class InstallerFrame(UIFrame):
    def __init__(self, master):
        super().__init__(master, width=master.cfg.width, height=master.cfg.height)

        self.current_stage = None
        self.staged_widgets = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Background
        self.canvas.grid(row=0, column=0)

        self.set_background_image(Config.get_resource_path(self) / f'background-image.jpg', width=master.cfg.width, height=master.cfg.height)

        # self.put(LauncherVersionText(self))

        # Top Panel
        self.put(TopBarFrame(self, self.canvas))

        # Bottom Panel
        self.put(BottomBarFrame(self, self.canvas, width=master.cfg.width, height=master.cfg.height)).grid(row=0, column=0, sticky='swe')

        # Action Panel
        self.put(CustomInstallationButton(self))
        self.put(InstallButton(self))

        # Application Events
        self.subscribe(
            Events.Application.Ready,
            lambda event: Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.Ready)))
        self.subscribe(
            Events.PackageManager.InitializeDownload,
            lambda event: Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.Download)))
        self.subscribe(
            Events.Application.Busy,
            lambda event: Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.Busy)))


class MainActionButton(UIImageButton):
    def __init__(self, **kwargs):
        self.command = kwargs['command']
        defaults = {}
        defaults.update(
            height=64,
            button_normal_opacity=0.95,
            button_hover_opacity=1,
            button_normal_brightness=0.95,
            button_hover_brightness=1,
            button_selected_brightness=0.8,
            bg_normal_opacity=0.95,
            bg_hover_opacity=1,
            bg_normal_brightness=0.95,
            bg_hover_brightness=1,
            bg_selected_brightness=0.8,
        )
        defaults.update(kwargs)
        super().__init__(**defaults)


class InstallButton(MainActionButton):
    def __init__(self, master):
        super().__init__(
            x=427,
            y=400,
            width=32,
            height=32,
            # button_image_path='button-start.png',
            # button_x_offset=-14,
            bg_image_path='button-start-background.png',
            bg_width=292,
            bg_height=52,
            text='Quick Installation',
            text_x_offset=0,
            text_y_offset=-1,
            font=('Microsoft YaHei', 14, 'bold'),
            command=self.install,
            master=master)
        self.subscribe(Events.GUI.InstallerFrame.StageUpdate, self.handle_stage_update)

    def handle_stage_update(self, event):
        self.stage = event.stage
        self.show(self.stage == Stage.Ready)

    def install(self):
        Events.Fire(Events.Application.InstallLauncher())


class CustomInstallationButton(MainActionButton):
    def __init__(self, master):
        super().__init__(
            x=427,
            y=450,
            width=32,
            height=32,
            # bg_image_path='button-start-background.png',
            # bg_width=292,
            # bg_height=52,
            text='Custom Installation',
            text_x_offset=0,
            text_y_offset=-1,
            font=('Microsoft YaHei', 11),
            command=lambda: Events.Fire(Events.GUI.InstallerFrame.StageUpdate(Stage.CustomInstall)),
            fill='#dddddd',
            activefill='#ffffff',
            master=master)
        self.stage = None
        self.subscribe(Events.GUI.InstallerFrame.StageUpdate, self.handle_stage_update)

    def handle_stage_update(self, event):
        self.stage = event.stage
        self.show(self.stage == Stage.Ready)


class LauncherVersionText(UIText):
    def __init__(self, master):
        super().__init__(x=20,
                         y=680,
                         text='',
                         font=('Roboto', 14),
                         fill='#bbbbbb',
                         activefill='#cccccc',
                         anchor='nw',
                         master=master)
        self.subscribe_set(
            Events.PackageManager.VersionNotification,
            lambda event: f'{event.package_states["Launcher"].installed_version}')
        self.subscribe_show(
            Events.GUI.InstallerFrame.StageUpdate,
            lambda event: event.stage == Stage.Ready)


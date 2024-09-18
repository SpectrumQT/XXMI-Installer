import winshell
import pythoncom
import subprocess

from dataclasses import dataclass
from pathlib import Path

import core.path_manager as Paths
import core.event_manager as Events
import core.config_manager as Config

from core.package_manager import Package, PackageMetadata

from core.utils.process_tracker import wait_for_process, wait_for_process_exit, WaitResult


@dataclass
class LauncherManagerEvents:

    @dataclass
    class AssertInstallationFolder:
        installation_folder: str

    @dataclass
    class StartCreateShortcuts:
        pass

    @dataclass
    class StartLauncher:
        asset_name: str


@dataclass
class LauncherManagerConfig:
    auto_update: bool = True
    installation_dir: str = ''
    create_shortcut: bool = True
    instance: str = ''


class LauncherPackage(Package):
    def __init__(self):
        super().__init__(PackageMetadata(
            package_name='Launcher',
            auto_load=True,
            github_repo_owner='SpectrumQT',
            github_repo_name='XXMI-Launcher',
            asset_version_pattern=r'.*(\d\.\d\.\d).*',
            asset_name_format='XXMI-LAUNCHER-PACKAGE-v%s.zip',
            signature_pattern=r'^## Signature[\r\n]+- ((?:[A-Za-z0-9+\/]{4})*(?:[A-Za-z0-9+\/]{4}|[A-Za-z0-9+\/]{3}=|[A-Za-z0-9+\/]{2}={2})$)',
            signature_public_key='MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAEYac352uRGKZh6LOwK0fVDW/TpyECEfnRtUp+bP2PJPP63SWOkJ3a/d9pAnPfYezRVJ1hWjZtpRTT8HEAN/b4mWpJvqO43SAEV/1Q6vz9Rk/VvRV3jZ6B/tmqVnIeHKEb',
            exit_after_update=True,
        ))
        Events.Subscribe(Events.LauncherManager.AssertInstallationFolder,
                         lambda event: self.assert_installation_folder(event.installation_folder))

    def download_latest_version(self):
        self.package_path = Path(Config.Launcher.installation_dir) / 'Resources' / 'Packages' / self.metadata.package_name
        super().download_latest_version()

    def get_installed_version(self):
        return '0.0.0'

    def install_latest_version(self, clean):
        Events.Fire(Events.PackageManager.InitializeInstallation())

        self.stop_launcher()

        Events.Fire(Events.Application.StatusUpdate(status='Deploying files...'))
        self.move_contents(self.downloaded_asset_path, Path(Config.Launcher.installation_dir))

        if Config.Launcher.create_shortcut:
            self.create_shortcut()

        self.start_launcher()

    def assert_installation_folder(self, installation_folder: str):
        installation_path = Path(installation_folder)

        Paths.can_create_dir(installation_path)

        folder_names = ['Wuthering Waves Game', 'ZenlessZoneZero Game', 'HonkaiStarRail', 'Genshin Impact game']
        for folder_name in folder_names:
            if folder_name in str(installation_path):
                raise ValueError(f'Installation folder must be located outside of `{folder_name}` folder!')

        exe_names = ['launcher.exe', 'launcher_epic.exe', 'Wuthering Waves.exe', 'Client-Win64-Shipping.exe', 'ZenlessZoneZero.exe', 'StarRail.exe', 'GenshinImpact.exe']
        for exe_name in exe_names:
            if Path(installation_path / exe_name).exists():
                raise ValueError(f'Installation folder must be located outside of folder with `{exe_name}` file!')

    def stop_launcher(self):
        Events.Fire(Events.Application.WaitForProcessExit(process_name='XXMI Launcher.exe'))

        result, pid = wait_for_process_exit('XXMI Launcher.exe', timeout=10, kill_timeout=5)
        if result == WaitResult.Timeout:
            Events.Fire(Events.Application.ShowError(
                modal=True,
                message='Failed to terminate XXMI Launcher.exe!\n\n'
                        'Please close it manually and press [OK] to continue.',
            ))

    def create_shortcut(self):
        Events.Fire(Events.LauncherManager.StartCreateShortcuts())
        pythoncom.CoInitialize()
        with winshell.shortcut(str(Path(winshell.desktop()) / 'XXMI Launcher.lnk')) as link:
            link.path = str(Path(Config.Launcher.installation_dir) / 'XXMI Launcher.exe')
            link.description = "Shortcut to XXMI Launcher"
            link.working_directory = Config.Launcher.installation_dir

    def start_launcher(self):
        launcher_path = Path(Config.Launcher.installation_dir) / 'XXMI Launcher.exe'
        Events.Fire(Events.LauncherManager.StartLauncher(asset_name=launcher_path.name))
        if not launcher_path.exists():
            raise ValueError(f'Failed to locate {launcher_path.name}!\nWas it removed by your Antivirus software?')
        if Config.Launcher.instance:
            subprocess.Popen([launcher_path, '--update', '--xxmi', Config.Launcher.instance])
        else:
            subprocess.Popen([launcher_path, '--update'])
        result, pid = wait_for_process(launcher_path.name, timeout=15, with_window=True)
        if result == WaitResult.Timeout:
            raise ValueError('Failed to start XXMI Launcher.exe!\n\n'
                             'Installation failed or was blocked by Antivirus software.')

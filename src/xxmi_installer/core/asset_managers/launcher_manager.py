import sys
import shutil
import winshell
import pythoncom
import subprocess
import time

from dataclasses import dataclass
from pathlib import Path
from win32api import GetFileVersionInfo, HIWORD, LOWORD

import core.path_manager as Paths
import core.event_manager as Events

from core.update_manager import Package, PackageMetadata

from core.utils.process_tracker import wait_for_process, wait_for_process_exit, WaitResult


@dataclass
class LauncherManagerEvents:

    @dataclass
    class StartCreateShortcuts:
        pass

    @dataclass
    class StartLauncher:
        asset_name: str


@dataclass
class LauncherManagerConfig:
    installation_dir: str = ''
    create_shortcut: bool = True
    instance: str = ''


class LauncherPackage(Package):
    def __init__(self, manager_cfg: LauncherManagerConfig):
        super().__init__(PackageMetadata(
            package_name='Installer',
            github_repo_owner='SpectrumQT',
            github_repo_name='XXMI-Launcher',
            asset_version_pattern=r'.*(\d\.\d\.\d).*',
            asset_name_format='XXMI-LAUNCHER-PACKAGE-v%s.zip',
            signature_pattern=r'^## Signature[\r\n]+- ((?:[A-Za-z0-9+\/]{4})*(?:[A-Za-z0-9+\/]{4}|[A-Za-z0-9+\/]{3}=|[A-Za-z0-9+\/]{2}={2})$)',
            signature_public_key='MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAEYac352uRGKZh6LOwK0fVDW/TpyECEfnRtUp+bP2PJPP63SWOkJ3a/d9pAnPfYezRVJ1hWjZtpRTT8HEAN/b4mWpJvqO43SAEV/1Q6vz9Rk/VvRV3jZ6B/tmqVnIeHKEb',
            exit_after_update=True,
        ))
        self.manager_cfg = manager_cfg

    def get_installed_version(self):
        return '0.0.0'

    def get_version_number(self, file_path, max_parts=4):
        version_info = GetFileVersionInfo(str(file_path), "\\")

        ms_file_version = version_info['FileVersionMS']
        ls_file_version = version_info['FileVersionLS']

        version = [str(HIWORD(ms_file_version)), str(LOWORD(ms_file_version)),
                   str(HIWORD(ls_file_version)), str(LOWORD(ls_file_version))]

        return '.'.join(version[:max_parts])

    def install_latest_version(self, clean):
        Events.Fire(Events.UpdateManager.InitializeInstallation())

        installation_path = Path(self.manager_cfg.installation_dir)

        self.stop_launcher()

        self.unpack_downloaded_asset(installation_path)

        if getattr(sys, 'frozen', False):
            self.copy_self_to_resources()

        if self.manager_cfg.create_shortcut:
            self.create_shortcuts()

        self.start_launcher()

    def stop_launcher(self):
        Events.Fire(Events.Application.WaitForProcessExit(asset_name='XXMI Launcher.exe'))

        result, pid = wait_for_process_exit('XXMI Launcher.exe', timeout=10, kill_timeout=5)
        if result == WaitResult.Timeout:
            Events.Fire(Events.Application.ShowError(
                modal=True,
                message='Failed to terminate XXMI Launcher.exe!\n\n'
                        'Please close it manually and press [OK] to continue.',
            ))

    def copy_self_to_resources(self):
        Events.Fire(Events.UpdateManager.StartFileWrite(asset_name='XXMI-Installer.exe'))
        assets_path = Path(self.manager_cfg.installation_dir) / 'Resources' / 'Packages' / 'Installer'
        updater_path = assets_path / 'XXMI-Installer.exe'
        if updater_path.exists():
            updater_version = self.get_version_number(updater_path)
            self_version = self.get_version_number(sys.executable)
            if self_version <= updater_version:
                return
        assets_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sys.executable, updater_path)

    def create_shortcuts(self):
        Events.Fire(Events.LauncherManager.StartCreateShortcuts())
        pythoncom.CoInitialize()
        with winshell.shortcut(str(Path(winshell.desktop()) / 'XXMI Launcher.lnk')) as link:
            link.path = str(Path(self.manager_cfg.installation_dir) / 'XXMI Launcher.exe')
            link.description = "Shortcut to XXMI Launcher"
            link.working_directory = self.manager_cfg.installation_dir

    def start_launcher(self):
        launcher_path = Path(self.manager_cfg.installation_dir) / 'XXMI Launcher.exe'
        Events.Fire(Events.LauncherManager.StartLauncher(asset_name=launcher_path.name))
        if not launcher_path.exists():
            raise ValueError(f'Failed to locate {launcher_path.name}!\nWas it removed by your Antivirus software?')
        subprocess.Popen([launcher_path, '--update', '--xxmi', self.manager_cfg.instance])
        result, pid = wait_for_process(launcher_path.name, timeout=15, with_window=True)
        if result == WaitResult.Timeout:
            raise ValueError('Failed to start XXMI Launcher.exe!\n\n'
                             'Installation failed or was blocked by Antivirus software.')


class LauncherManager:
    def __init__(self, cfg: LauncherManagerConfig):
        self.cfg = cfg
        self.package = LauncherPackage(cfg)

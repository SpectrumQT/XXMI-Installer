import shutil
import logging
import time
import re

from dataclasses import dataclass, field
from typing import Union, List, Dict
from pathlib import Path

log = logging.getLogger(__name__)

import core.event_manager as Events
import core.path_manager as Paths

from core.utils.security import Security
from core.utils.github_client import GitHubClient


@dataclass
class PackageMetadata:
    package_name: str
    github_repo_owner: str
    github_repo_name: str
    asset_version_pattern: str
    asset_name_format: str
    signature_pattern: str
    signature_public_key: str
    exit_after_update: bool = False


@dataclass
class PackageConfig:
    latest_version: str = ''
    skipped_version: str = ''
    update_check_time: int = 0


class Package:
    def __init__(self, metadata: PackageMetadata):
        self.metadata = metadata
        self.cfg: Union[PackageConfig, None] = None
        self.asset_version_pattern = re.compile(self.metadata.asset_version_pattern)
        self.signature_pattern = re.compile(self.metadata.signature_pattern, re.MULTILINE)

        self.security = Security(public_key=self.metadata.signature_public_key)
        self.github_client = GitHubClient(owner=self.metadata.github_repo_owner, repo=self.metadata.github_repo_name)

        self.active = True
        self.installed_version: str = ''
        self.state: PackageConfig
        self.download_url: str = ''
        self.signature: Union[str, None] = None

        self.downloaded_asset_path: Union[Path, None] = None
        self.installed_asset_path: Union[Path, None] = None

    def get_installed_version(self) -> str:
        raise NotImplementedError(f'Method "get_installed_version" is not implemented for package {self.metadata.package_name}!')

    def detect_installed_version(self):
        try:
            self.installed_version = self.get_installed_version()
        except Exception as e:
            self.installed_version = ''
            raise ValueError(f'Failed to detect installed {self.metadata.package_name} version:\n\n{e}') from e

    def get_latest_version(self) -> (str, str, Union[str, None]):
        version, url, signature = self.github_client.fetch_latest_release(self.asset_version_pattern,
                                                                          self.metadata.asset_name_format,
                                                                          self.signature_pattern)
        return version, url, signature

    def detect_latest_version(self):
        try:
            self.cfg.latest_version, self.download_url, self.signature = self.get_latest_version()
        except Exception as e:
            self.cfg.latest_version, self.download_url, self.signature = '', '', ''
            raise ValueError(f'Failed to detect latest {self.metadata.package_name} version:\n\n{e}') from e

    def update_available(self):
        return self.cfg.latest_version != '' and self.installed_version != self.cfg.latest_version

    def download_latest_version(self):
        self.downloaded_asset_path = None

        Events.Fire(Events.UpdateManager.InitializeDownload())

        asset_file_name = self.metadata.asset_name_format % self.cfg.latest_version

        Events.Fire(Events.UpdateManager.StartDownload(asset_name=asset_file_name))

        data = self.github_client.download_data(self.download_url, block_size=128*1024, 
                                                update_progress_callback=self.notify_download_progress)

        Events.Fire(Events.UpdateManager.InitializeInstallation())

        Events.Fire(Events.UpdateManager.StartIntegrityVerification(asset_name='downloaded data'))

        if not self.security.verify(self.signature, data):
            raise ValueError(f'Downloaded data integrity verification failed!\n'
                             'Please restart the launcher and try again!')

        Events.Fire(Events.UpdateManager.StartFileWrite(asset_name=asset_file_name))

        asset_path = Paths.App.Downloads / asset_file_name
        with open(asset_path, 'wb') as f:
            f.write(data)

        Events.Fire(Events.UpdateManager.StartIntegrityVerification(asset_name=asset_file_name))

        with open(asset_path, 'rb') as f:
            if not self.security.verify(self.signature, f.read()):
                raise ValueError(f'{asset_path.name} data integrity verification failed!\n'
                                 'Please restart the launcher and try again!')

        self.downloaded_asset_path = asset_path

    @staticmethod
    def notify_download_progress(downloaded_bytes, total_bytes):
        Events.Fire(Events.UpdateManager.UpdateDownloadProgress(
            downloaded_bytes=downloaded_bytes,
            total_bytes=total_bytes,
        ))

    def unpack_downloaded_asset(self, destination_path: Path):
        Events.Fire(Events.UpdateManager.StartUnpack(asset_name=self.downloaded_asset_path.name))
        shutil.unpack_archive(self.downloaded_asset_path, destination_path)
        self.downloaded_asset_path.unlink()

    def install_latest_version(self, clean):
        raise NotImplementedError(f'Method "install_latest_version" is not implemented for package {self.metadata.package_name}!')

    def update(self, clean=False):
        self.download_latest_version()
        self.install_latest_version(clean=clean)
        self.detect_installed_version()


@dataclass
class PackageState:
    installed_version: str
    latest_version: str
    skipped_version: str


@dataclass
class UpdateManagerConfig:
    packages: Dict[str, PackageConfig] = field(default_factory=lambda: {})
    auto_update: bool = True


@dataclass
class UpdateManagerEvents:

    @dataclass
    class VersionNotification:
        auto_update: bool
        package_states: Dict[str, PackageState]

    @dataclass
    class InitializeDownload:
        pass

    @dataclass
    class StartDownload:
        asset_name: str

    @dataclass
    class UpdateDownloadProgress:
        downloaded_bytes: int
        total_bytes: int

    @dataclass
    class StartIntegrityVerification:
        asset_name: str

    @dataclass
    class StartFileWrite:
        asset_name: str

    @dataclass
    class StartFileMove:
        asset_name: str

    @dataclass
    class InitializeInstallation:
        pass

    @dataclass
    class StartUnpack:
        asset_name: str


class UpdateManager:
    def __init__(self, app, cfg: UpdateManagerConfig, packages: List[Package]):
        self.app = app
        self.cfg = cfg
        self.packages = packages

        # Fast detection of installed packages versions, with latest_version read from config file
        # It enables fast (but 1 launch delayed) update detection for --nogui mode
        for package in self.packages:
            package.detect_installed_version()
            if package.metadata.package_name not in self.cfg.packages:
                self.cfg.packages[package.metadata.package_name] = PackageConfig()

            package.cfg = self.cfg.packages[package.metadata.package_name]

    def get_version_notification(self) -> UpdateManagerEvents.VersionNotification:
        return UpdateManagerEvents.VersionNotification(
            auto_update=self.cfg.auto_update,
            package_states={
                package.metadata.package_name: PackageState(
                    installed_version=package.installed_version,
                    latest_version=package.cfg.latest_version,
                    skipped_version=package.cfg.skipped_version,
                ) for package in self.packages if package.active
            },
        )

    def notify_package_versions(self):
        self.app.config_manager.save_config()
        Events.Fire(self.get_version_notification())

    def update_available(self):
        for package in self.packages:
            if package.update_available():
                return True

    def update_packages(self, no_install=False, force=False, reinstall=False, packages=None):

        for package in self.packages:

            # Skip package processing if it's not active, intended for multiple model importers support
            if not package.active:
                continue

            # Skip package processing if it's name isn't listed in provided package list
            if packages is not None and package.metadata.package_name not in packages:
                continue

            # Check if installation is pending, as we'll need download url from update check
            install = not no_install and (package.update_available() or reinstall) and (self.cfg.auto_update or force)

            # Check local files for the installed package version
            package.detect_installed_version()

            # Query GitHub for the latest available package version
            current_time = int(time.time())
            # Force update check if installation is pending or the last check time is somewhere in the future
            force_check = install or package.cfg.update_check_time > current_time
            # We're going to throttle query to 1 per hour by default, else user can be temporary banned by GitHub
            if force_check or package.cfg.update_check_time + 3600 < current_time:
                package.detect_latest_version()
                package.cfg.update_check_time = current_time

            # Check if installation is pending again, as update check may find new version
            install = not no_install and (package.update_available() or reinstall) and (self.cfg.auto_update or force)

            # Versions checking is complete, lets exit early if update installation is not required
            if not install:
                continue

            # Download and install the latest package version, it can take a while
            package.update(clean=reinstall)

            if package.metadata.exit_after_update:
                Events.Fire(Events.Application.Close(delay=500))
                return

        self.notify_package_versions()

    def skip_latest_updates(self):
        for package in self.packages:
            package.cfg.skipped_version = package.cfg.latest_version

import os
import json

from pathlib import Path
from dataclasses import dataclass, field, fields
from typing import Union, Dict, Any

from dacite import from_dict

import core.path_manager as Paths
import core.event_manager as Events

from core import package_manager
from core.packages import launcher_package


@dataclass
class SecurityConfig:
    user_signature: str = ''


@dataclass
class AppConfig:
    # Config fields
    Launcher: launcher_package.LauncherManagerConfig = field(
        default_factory=lambda: launcher_package.LauncherManagerConfig()
    )
    Packages: package_manager.PackageManagerConfig = field(
        default_factory=lambda: package_manager.PackageManagerConfig()
    )
    # State fields
    # Active: Optional[WWMIConfig] = field(init=False, default=None)

    def as_dict(self, obj: Any) -> Dict[str, Any]:
        result = {}

        if hasattr(obj, '__dataclass_fields__'):
            # Process dataclass object
            for obj_field in fields(obj):
                # Fields with 'init=False' contain app state data that isn't supposed to be saved
                if not obj_field.init:
                    continue
                # Recursively process nested dataclass
                value = getattr(obj, obj_field.name)

                if hasattr(value, '__dataclass_fields__') or isinstance(value, dict | list | tuple):
                    result[obj_field.name] = self.as_dict(value)
                else:
                    result[obj_field.name] = value

        elif isinstance(obj, dict):
            # Process dict object
            for obj_field, value in obj.items():
                if hasattr(value, '__dataclass_fields__') or isinstance(value, dict | list | tuple):
                    result[obj_field] = self.as_dict(value)
                else:
                    result[obj_field] = value

        elif isinstance(obj, list | tuple):
            # Process list or tuple object
            result = []
            for value in obj:
                if hasattr(value, '__dataclass_fields__') or isinstance(value, dict | list | tuple):
                    result.append(self.as_dict(value))
                else:
                    result.append(value)

        return result

    def as_json(self):
        cfg = self.as_dict(self)
        return json.dumps(cfg, indent=4)

    def from_json(self, config_path: Path):
        cfg = self.as_dict(self)
        if config_path.is_file():
            with open(config_path, 'r') as f:
                cfg.update(json.load(f))
        for key, value in from_dict(data_class=AppConfig, data=cfg).__dict__.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def load(self):
        global Launcher
        Launcher = self.Launcher
        global Packages
        Packages = self.Packages


Config: AppConfig = AppConfig()

# Config aliases, intended to shorten dot names
Launcher: launcher_package.LauncherManagerConfig
Packages: package_manager.PackageManagerConfig


def get_resource_path(element):
    return Paths.App.Themes / 'Default' / element.get_resource_path()

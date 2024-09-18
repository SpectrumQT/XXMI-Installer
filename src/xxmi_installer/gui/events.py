
from dataclasses import dataclass
from enum import Enum, auto


class Stage(Enum):
    Ready = auto()
    CustomInstall = auto()
    Busy = auto()
    Download = auto()


@dataclass
class GUIEvents:

    @dataclass
    class InstallerFrame:

        @dataclass
        class StageUpdate:
            stage: Stage

        # @dataclass
        # class ToggleToolbox:
        #     show: bool = False
        #     hide_on_leave: bool = False
from enum import Enum, auto


class Stage(Enum):
    Initialization = auto()
    Configuration = auto()
    Download = auto()
    Installation = auto()

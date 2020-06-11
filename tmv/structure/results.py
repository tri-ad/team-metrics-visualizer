from enum import Enum, auto

# Results for squad health check
SHCResults = dict


# Result for one question in squad health check
class SHCResult(Enum):
    red = auto()
    amber = auto()
    green = auto()


# Story points
SP = float

from enum import Enum

class Status(Enum):
    UNKNOWN = 0
    VISITED = 1
    PRIVATE = 2
    MISSING = 3
    INCOMPLETE = 4
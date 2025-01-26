from enum import Enum

class AgentRole(Enum):
    HUNTER: int = 0
    CARTOGRAPHER: int = 1
    KNIGHT: int = 2
    BWL_STUDENT: int = 3


class AgentAction(Enum):
    MOVE_UP: int = 0
    MOVE_LEFT: int = 1
    MOVE_RIGHT: int = 2
    MOVE_DOWN: int = 3
    PICK_UP: int = 4
    SHOOT_UP: int = 5
    SHOOT_LEFT: int = 6
    SHOOT_RIGHT: int = 7
    SHOOT_DOWN: int = 8
    SHOUT: int = 9


class AgentItem(Enum):
    GOLD: int = 0
    ARROW: int = 1


class AgentGoal(Enum):
    GOLD: int = 0
    WUMPUS: int = 1
    MAP_PROGRESS: int = 2

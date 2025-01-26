from enum import Enum


class TileCondition(Enum):
    SAFE: int = 0
    WALL: int = 1
    SHINY: int = 2
    WUMPUS: int = 3
    PREDICTED_WUMPUS: int = 4
    STENCH: int = 5
    PIT: int = 6
    PREDICTED_PIT: int = 7
    BREEZE: int = 8

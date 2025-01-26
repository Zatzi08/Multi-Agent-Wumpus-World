from enum import Enum

class RequestObject(Enum):
    GOLD = 1
    TILE_INFORMATION = 2
    KILL_WUMPUS = 3


class ResponseType(Enum):
    ACCEPT = 1
    DENY = 2
    COUNTEROFFER = 3


class OfferedObjects:
    def __init__(self, gold_amount: int, tile_information: list[tuple[int, int, list]],
                 wumpus_positions: list[tuple[int, int]]):
        self.gold_amount = gold_amount
        self.tile_information = tile_information
        self.wumpus_positions = wumpus_positions

class RequestedObjects:
    def __init__(self, gold: int, tiles: list[tuple[int, int]], wumpus_positions: int):
        self.gold: int = gold
        self.tiles: list[tuple[int, int]] = tiles
        self.wumpus_positions: int = wumpus_positions


class Offer:
    def __init__(self, offered_objects: OfferedObjects, requested_objects: RequestedObjects, offer_role):
        # TODO create offer from OfferedObjects and RequestedObjects
        self.off_gold: int = offered_objects.gold_amount
        self.off_tiles: set[(int, int)] = {(x, y) for x, y, z in offered_objects.tile_information}
        self.off_wumpus_positions: set[(int, int)] = {(x, y) for x, y, z in offered_objects.wumpus_positions}
        self.off_role = offer_role

        self.req_gold: int = requested_objects.gold
        self.req_tiles: list[tuple[int, int]] = requested_objects.tiles
        self.req_wumpus_positions: int = requested_objects.wumpus_positions

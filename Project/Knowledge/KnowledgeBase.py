from enum import Enum
from typing import cast
from numpy.typing import NDArray
import numpy


class TileCondition(Enum):
    SAFE: 0
    WALL: 1
    SHINY: 2
    WUMPUS: 3
    PREDICTED_WUMPUS: 4
    STENCH: 5
    PIT: 6
    PREDICTED_PIT: 7
    BREEZE: 8


class _Tile:
    def __init__(self):
        self.__visited: bool = False
        self.__size: int = len(TileCondition)
        self.__bitmask: int = int('0' * len(TileCondition), 2)

    def add(self, condition: TileCondition):
        self.__bitmask |= 1 << condition.value()

    def has(self, condition: TileCondition) -> bool:
        return self.__bitmask & 1 << condition.value() is True

    def remove(self, condition: TileCondition):
        self.__bitmask &= ~(1 << condition.value())

    def get_conditions(self) -> list[TileCondition]:
        return [condition for condition in TileCondition if self.has(condition)]

    def set_visited(self):
        self.__visited = True

    def visited(self) -> bool:
        return self.__visited


class _Map:
    def __init__(self, map_width: int, map_height: int):
        self.__width: int = map_width
        self.__height: int = map_height
        self.__map = NDArray[NDArray[_Tile]] = numpy.array(
            [[_Tile() for _ in range(map_height)] for _ in range(map_width)],
            dtype=object
        )
        # add map border (walls)
        for x in range(map_width):
            cast(_Tile, self.__map[x, 0]).add(TileCondition.WALL)
            cast(_Tile, self.__map[x, map_height-1]).add(TileCondition.WALL)
        for y in range(map_height):
            cast(_Tile, self.__map[0, y]).add(TileCondition.WALL)
            cast(_Tile, self.__map[map_width-1, y]).add(TileCondition.WALL)

    def access(self, x: int, y: int) -> _Tile:
        return cast(_Tile, self.__map[x][y])


SURROUNDING_TILES = {(-1, 0), (1, 0), (0, -1), (0, 1)}


class KnowledgeBase:
    def __init__(self, name: str, map_width: int, map_height: int, position: tuple[int, int]):
        #
        # POSITION
        #

        self.__position: tuple[int, int] = position

        #
        # MAP
        #

        self.__map: _Map = _Map(map_width, map_height)

        #
        # AGENTS
        #

        self.__name: str = name  # name of agent owning this knowledge base
        self.__agents = set()  # info about agents

    #
    # POSITION
    #

    def update_position(self, x: int, y: int):
        """updates own position"""
        self.__position = (x, y)

    def get_position(self) -> tuple[int, int]:
        """returns own position"""
        return self.__position[0], self.__position[1]

    #
    # MAP
    #

    def __add_condition_if_all_surrounding_tiles_allow(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS, TileCondition.PREDICTED_PIT}) -> bool:
        """adds (predicted) dangers if no adjacent tile disallows it"""
        # get tile condition that the surrounding tiles have to fulfill
        if tile_condition == TileCondition.PREDICTED_PIT:
            surrounding_tiles_condition = TileCondition.BREEZE
        else:
            surrounding_tiles_condition = TileCondition.STENCH

        # check if all surrounding tiles fulfill the test condition
        count = 0
        for position in SURROUNDING_TILES:
            if self.__map.access(x + position[0], y + position[1]).has(surrounding_tiles_condition):
                count += 1
                continue
            # do not have to check for walls and pits independently as they cannot be visited
            if self.__map.access(x + position[0], y + position[1]).visited():
                break
            count += 1
        if count == 4:
            self.__map.access(x, y).add(tile_condition)
            return True
        return False

    def __predict(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.PREDICTED_WUMPUS, TileCondition.PREDICTED_PIT}) -> bool:
        """predicts dangers"""
        # check if prediction is already made
        if self.__map.access(x, y).has(tile_condition):
            return True

        # get check parameters
        if tile_condition == TileCondition.PREDICTED_PIT:
            tile_check_1 = TileCondition.PIT
            tile_check_2 = TileCondition.WUMPUS
        else:
            tile_check_1 = TileCondition.WUMPUS
            tile_check_2 = TileCondition.PIT

        # check if knowledge is already known
        if self.__map.access(x, y).has(tile_check_1):
            return True

        # skip if prediction is not consistent
        if (self.__map.access(x, y).has(TileCondition.SAFE)
                or self.__map.access(x, y).has(TileCondition.WALL)
                or self.__map.access(x, y).has(tile_check_2)):
            return False

        # add, if consistent with surrounding tiles
        return self.__add_condition_if_all_surrounding_tiles_allow(x, y, tile_condition)

    def __add_stench_or_breeze(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.STENCH, TileCondition.BREEZE}) -> bool:
        """adds stenches or breezes if possible, then predicts dangers"""
        # check if stench or breeze is already placed
        if self.__map.access(x, y).has(tile_condition):
            return True

        # add, if not wall or pit
        if (self.__map.access(x, y).has(TileCondition.WALL)
                or self.__map.access(x, y).has(TileCondition.PIT)):
            return False
        self.__map.access(x, y).add(tile_condition)

        # get danger types that are to be found
        if tile_condition == TileCondition.STENCH:
            predicted_danger = TileCondition.PREDICTED_WUMPUS
            real_danger = TileCondition.WUMPUS
        else:
            predicted_danger = TileCondition.PREDICTED_PIT
            real_danger = TileCondition.PIT

        # predict surrounding dangers
        count = 0
        for position in SURROUNDING_TILES:
            # count if surrounding tile could be (or is) wumpus
            if self.__predict(x + position[0], y + position[1], predicted_danger):
                count += 1
        if count == 0:
            # for breezes there cannot be 0
            # for stenches: remove if 0 (stench cannot be there anymore)
            self.__map.access(x, y).remove(TileCondition.STENCH)
        elif count == 1:
            # resolve, as predicted danger is real (prediction is correct)
            for position in SURROUNDING_TILES:
                if self.__map.access(x + position[0], y + position[1]).has(predicted_danger):
                    self.__map.access(x + position[0], y + position[1]).remove(predicted_danger)
                    self.update_tile(x + position[0], y + position[1], real_danger)
                    return True
        return True

    def __discard_and_re_predict(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS, TileCondition.PREDICTED_PIT}):
        """discards (predicted) dangers, then re-evaluates stenches and danger predictions accordingly"""
        if self.__map.access(x, y).has(tile_condition):
            # discard danger
            self.__map.access(x, y).remove(tile_condition)

            # get tile condition to re-predict
            if tile_condition == TileCondition.PREDICTED_PIT:
                prediction_condition = TileCondition.BREEZE
            else:
                prediction_condition = TileCondition.STENCH

            # (if possible) remove or re-predict surroundings
            for position in SURROUNDING_TILES:
                if self.__map.access(x + position[0], y + position[1]).has(prediction_condition):
                    self.__map.access(x + position[0], y + position[1]).remove(prediction_condition)
                    self.__add_stench_or_breeze(x + position[0], y + position[1], prediction_condition)

    def update_tile(self, x: int, y: int, tile_conditions: [TileCondition]):
        """updates map knowledge given some knowledge about a tile"""
        # developer has to make sure that all (missing) tile conditions are listed on visit
        if (x, y) == self.__position:
            self.__map.access(x, y).set_visited()

        # for every condition: check for consistency and potentially add it
        for new_tile_condition in tile_conditions:
            # filter already known conditions
            if self.__map.access(x, y).has(new_tile_condition):
                continue

            # consistency
            match new_tile_condition:
                case TileCondition.SAFE:
                    # add
                    self.__map.access(x, y).add(TileCondition.SAFE)

                    # remove (predicted) dangers as the tile is safe now
                    self.__discard_and_re_predict(x, y, TileCondition.WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)
                case TileCondition.WALL:
                    # remove predicted dangers as the tile is a wall
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.access(x, y).add(TileCondition.WALL)
                case TileCondition.SHINY:
                    # add
                    self.__map.access(x, y).add(TileCondition.SHINY)
                case TileCondition.WUMPUS:
                    # if tile is safe already, wumpus is already gone
                    if self.__map.access(x, y).has(TileCondition.SAFE):
                        continue

                    # remove predictions as there is a resolution now
                    self.__map.access(x, y).remove(TileCondition.PREDICTED_WUMPUS)
                    self.__map.access(x, y).remove(TileCondition.PREDICTED_PIT)

                    # add, if all surrounding tiles could be stenches
                    if self.__add_condition_if_all_surrounding_tiles_allow(x, y, TileCondition.WUMPUS):
                        # wumpus added: place stenches around wumpus
                        for position in SURROUNDING_TILES:
                            self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.STENCH)
                    else:
                        # wumpus not added: tile must be safe now
                        self.__map.access(x, y).add(TileCondition.SAFE)

                        # remove surrounding stenches if possible
                        for position in SURROUNDING_TILES:
                            if self.__map.access(x + position[0], y + position[1]).has(TileCondition.STENCH):
                                self.__map.access(x + position[0], y + position[1]).remove(TileCondition.STENCH)
                                self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.STENCH)
                case TileCondition.PREDICTED_WUMPUS:
                    # predict wumpus
                    self.__predict(x, y, TileCondition.PREDICTED_WUMPUS)
                case TileCondition.STENCH:
                    # try adding and (on add) predict wumpus
                    self.__add_stench_or_breeze(x, y, TileCondition.STENCH)
                case TileCondition.PIT:
                    # remove predicted dangers as the tile is a pit
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__map.access(x, y).remove(TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.access(x, y).add(TileCondition.PIT)

                    # place breezes around pit
                    for position in SURROUNDING_TILES:
                        self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.BREEZE)
                case TileCondition.PREDICTED_PIT:
                    # predict pit
                    self.__predict(x, y, TileCondition.PREDICTED_PIT)
                case TileCondition.BREEZE:
                    # add and predict pits
                    self.__add_stench_or_breeze(x, y, TileCondition.BREEZE)
        return

    def visited(self, x: int, y: int) -> bool:
        """returns whether a certain tile has been visited"""
        return self.__map.access(x, y).visited()

    def get_tile(self, x: int, y: int) -> list[TileCondition]:
        """returns all information about a tile"""
        return self.__map.access(x, y).get_conditions()

    def tile_has_condition(self, x: int, y: int, tile_condition: TileCondition) -> bool:
        return self.__map.access(x, y).has(tile_condition)

    #
    # AGENTS
    #

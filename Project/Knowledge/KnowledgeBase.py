from enum import Enum


class TileCondition(Enum):
    SAFE: 1
    WALL: 2
    SHINY: 3
    WUMPUS: 4
    PREDICTED_WUMPUS: 5
    STENCH: 6
    PIT: 7
    PREDICTED_PIT: 8
    BREEZE: 9


SURROUNDING_TILES = {(-1, 0), (1, 0), (0, -1), (0, 1)}


class KnowledgeBase:
    def __init__(self, name: str):
        # POSITION
        self.__position: tuple[int, int] = (0, 0)  # position on map, (0, 0) is personal starting point
        # MAP
        self.__tile_exists: set[tuple[int, int]] = set()  # existing tiles
        self.__tile_visited: set[tuple[int, int]] = set()  # visited tiles
        self.__map: set[tuple[int, int, TileCondition]] = set()  # personal map
        # map contributions: name + time, needed if lies are allowed
        # AGENTS
        self.__name: str = name  # name of agent owning this knowledge base
        self.__agents = set()  # info about agents
        # trust in agents: name + trust_number, needed if lies are allowed

    #
    # POSITION
    #

    def update_position(self, x: int, y: int):
        """updates own position"""
        self.__position = (x, y)
        return

    def get_position(self):
        """returns own position"""
        return self.__position[0], self.__position[1]

    #
    # MAP
    #

    def __add_condition_if_all_surrounding_tiles_allow(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS, TileCondition.PREDICTED_PIT}) -> bool:
        if tile_condition == TileCondition.PREDICTED_PIT:
            surrounding_tiles_condition = TileCondition.BREEZE
        else:
            surrounding_tiles_condition = TileCondition.STENCH
        count = 0
        for position in SURROUNDING_TILES:
            if (x + position[0], y + position[1], surrounding_tiles_condition) in self.__map:
                count += 1
                continue
            # do not have to check for walls and pits independently as they cannot be visited
            if (x + position[0], y + position[1]) in self.__tile_visited:
                break
            count += 1
        if count == 4:
            self.__map.add((x, y, tile_condition))
            return True
        return False

    def __predict(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.PREDICTED_WUMPUS, TileCondition.PREDICTED_PIT}) -> bool:
        # check if prediction is already made
        if (x, y, tile_condition) in self.__map:
            return True

        # get check parameters
        if tile_condition == TileCondition.PREDICTED_PIT:
            tile_check_1 = TileCondition.PIT
            tile_check_2 = TileCondition.WUMPUS
        else:
            tile_check_1 = TileCondition.WUMPUS
            tile_check_2 = TileCondition.PIT

        # check if knowledge is already known
        if (x, y, tile_check_1) in self.__map:
            return True

        # skip if prediction is not consistent
        if ((x, y, TileCondition.SAFE) in self.__map
                or (x, y, TileCondition.WALL) in self.__map
                or (x, y, tile_check_2) in self.__map):
            return False

        # add, if consistent with surrounding tiles
        return self.__add_condition_if_all_surrounding_tiles_allow(x, y, tile_condition)

    def __add_stench_or_breeze(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.STENCH, TileCondition.BREEZE}) -> bool:
        # check if stench or breeze is already placed
        if (x, y, tile_condition) in self.__map:
            return True

        # add, if exists and not on wall or pit
        if (not (x, y) in self.__tile_exists
                or (x, y, TileCondition.WALL) in self.__map
                or (x, y, TileCondition.PIT) in self.__map):
            return False
        self.__map.add((x, y, tile_condition))

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
            self.__map.discard((x, y, TileCondition.STENCH))
        elif count == 1:
            # resolve, as predicted danger is real (prediction is correct)
            for position in SURROUNDING_TILES:
                if (x + position[0], y + position[1], predicted_danger) in self.__map:
                    self.__map.discard((x + position[0], y + position[1], predicted_danger))
                    self.update_tile(x + position[0], y + position[1], real_danger)
                    return True
        return True

    def __discard_and_re_predict(self, x: int, y: int, tile_condition: TileCondition in {TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS, TileCondition.PREDICTED_PIT}):
        if (x, y, tile_condition) in self.__map:
            # discard
            self.__map.discard((x, y, tile_condition))

            if tile_condition == TileCondition.PREDICTED_PIT:
                prediction_condition = TileCondition.BREEZE
            else:
                prediction_condition = TileCondition.STENCH

            # (if possible) remove or re-predict surroundings
            for position in SURROUNDING_TILES:
                if (x + position[0], y + position[1], prediction_condition) in self.__map:
                    self.__map.discard((x + position[0], y + position[1], prediction_condition))
                    self.__add_stench_or_breeze(x + position[0], y + position[1], prediction_condition)

    def update_tile(self, x: int, y: int, tile_conditions: [TileCondition]):
        """updates an agents knowledge base given some knowledge about the map"""

        # add tile to the existing tiles
        self.__tile_exists.add((x, y))

        # developer has to make sure that all (missing) tile conditions are listed on visit
        if (x, y) == self.__position:
            if not (x, y) in self.__tile_visited:
                self.__tile_visited.add((x, y))

        # for every condition: check for consistency and potentially add it
        for new_tile_condition in tile_conditions:
            # filter already known conditions
            if (x, y, new_tile_condition) in self.__map:
                continue

            # consistency
            match new_tile_condition:
                case TileCondition.SAFE:
                    # add
                    self.__map.add((x, y, TileCondition.SAFE))

                    # remove (predicted) dangers as the tile is safe now
                    self.__discard_and_re_predict(x, y, TileCondition.WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)
                case TileCondition.WALL:
                    # remove predicted dangers as the tile is a wall
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.add((x, y, TileCondition.WALL))
                case TileCondition.SHINY:
                    # add
                    self.__map.add((x, y, TileCondition.SHINY))
                case TileCondition.WUMPUS:
                    # if tile is safe already, wumpus is already gone
                    if (x, y, TileCondition.SAFE) in self.__map:
                        continue

                    # remove predictions as there is a resolution now
                    self.__map.discard((x, y, TileCondition.PREDICTED_WUMPUS))
                    self.__map.discard((x, y, TileCondition.PREDICTED_PIT))

                    # add, if all surrounding tiles could be stenches
                    if self.__add_condition_if_all_surrounding_tiles_allow(x, y, TileCondition.WUMPUS):
                        # wumpus added: place stenches around wumpus
                        for position in SURROUNDING_TILES:
                            self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.STENCH)
                    else:
                        # wumpus not added: tile must be safe now
                        self.__map.add((x, y, TileCondition.SAFE))

                        # remove surrounding stenches if possible
                        for position in SURROUNDING_TILES:
                            if (x + position[0], y + position[1], TileCondition.STENCH) in self.__map:
                                self.__map.discard((x + position[0], y + position[1], TileCondition.STENCH))
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
                    self.__map.discard((x, y, TileCondition.PREDICTED_PIT))

                    # add
                    self.__map.add((x, y, TileCondition.PIT))

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

    def visited(self, x: int, y: int):
        return (x, y) in self.__tile_visited

    def get_tile(self, x: int, y: int) -> list[TileCondition]:
        if (x, y) in self.__tile_exists:
            condition_list = []
            for tile_condition in TileCondition:
                if (x, y, tile_condition) in self.__map:
                    condition_list.append(tile_condition)
            return condition_list

    #
    # AGENTS
    #

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


SURROUNDING_TILES = {(-1, 0), (1, 0), (0, -1), (0, 1)}


class _Map:
    def __init__(self, map_width: int, map_height: int):
        self.__map: list[list[set[TileCondition]]] = [[set()] * map_height] * map_width
        self.__visited_map: list[list[bool]] = [[False] * map_height] * map_width
        self.__tiles_by_tile_condition: list[set[tuple[int, int]]] = [set()] * len(TileCondition)
        self.__closest_unvisited_tiles: set[tuple[int, int]] = set()
        self.__closest_unknown_tiles_to_any_known_tiles: set[tuple[int, int]] = set()
        self.__shouts: dict[tuple[int, int], int] = {}
        self.__kill_wumpus_tasks: set[tuple[int, int]] = set()

        # add map border (walls)
        for x in range(map_width):
            self.__map[x][0].add(TileCondition.WALL)
            self.__map[x][map_height - 1].add(TileCondition.WALL)
        for y in range(map_height):
            self.__map[0][y].add(TileCondition.WALL)
            self.__map[map_width - 1][y].add(TileCondition.WALL)

    def __update_closest_unknown_tiles_using_new_tile(self, x: int, y: int) -> None:
        if TileCondition.WALL in self.__map[x][y]:
            return

        self.__closest_unknown_tiles_to_any_known_tiles.discard((x, y))

        for position in SURROUNDING_TILES:
            if not self.__map[x + position[0]][y + position[1]]:
                self.__closest_unknown_tiles_to_any_known_tiles.add((x + position[0], y + position[1]))

    def add_condition_to_tile(self, x: int, y: int, condition: TileCondition) -> None:
        self.__map[x][y].add(condition)
        self.__tiles_by_tile_condition[condition.value].add((x, y))
        self.__update_closest_unknown_tiles_using_new_tile(x, y)

    def tile_has_condition(self, x: int, y: int, condition: TileCondition) -> bool:
        return condition in self.__map[x][y]

    def remove_condition_from_tile(self, x: int, y: int, condition: TileCondition) -> None:
        self.__map[x][y].discard(condition)
        self.__tiles_by_tile_condition[condition.value].discard((x, y))

    def get_conditions_of_tile(self, x: int, y: int) -> set[TileCondition]:
        return self.__map[x][y]

    def set_visited(self, x: int, y: int) -> None:
        self.__visited_map[x][y] = True
        self.__closest_unvisited_tiles.discard((x, y))
        for position in SURROUNDING_TILES:
            if (self.visited(x + position[0], y + position[1])
                    or self.tile_has_condition(x + position[0], y + position[1], TileCondition.WALL)
                    or self.tile_has_condition(x + position[0], y + position[1], TileCondition.PIT)):
                continue
            self.__closest_unvisited_tiles.add((x + position[0], y + position[1]))

    def visited(self, x: int, y: int) -> bool:
        return self.__visited_map[x][y]

    def get_tiles_by_condition(self, condition: TileCondition) -> set[tuple[int, int]]:
        return self.__tiles_by_tile_condition[condition.value]

    def get_closest_unvisited_tiles(self) -> set[tuple[int, int]]:
        return self.__closest_unvisited_tiles

    def get_closest_unknown_tiles_to_any_known_tiles(self) -> set[tuple[int, int]]:
        return self.__closest_unknown_tiles_to_any_known_tiles

    def add_shout(self, x: int, y: int, time: int) -> None:
        self.__shouts[(x, y)] = time

    def get_shouts(self) -> dict[tuple[int, int], int]:
        return self.__shouts

    def remove_shout(self, x: int, y: int) -> None:
        if self.__shouts[(x, y)]:
            self.__shouts.pop((x, y))

    def add_kill_wumpus_task(self, x: int, y: int) -> None:
        self.__kill_wumpus_tasks.add((x, y))

    def get_kill_wumpus_tasks(self) -> set[tuple[int, int]]:
        for x, y in self.__kill_wumpus_tasks:
            if (TileCondition.SAFE in self.__map[x][y] or TileCondition.WALL in self.__map[x][y]
                    or TileCondition.PIT in self.__map[x][y] or TileCondition.STENCH in self.__map[x][y]):
                self.__kill_wumpus_tasks.discard((x, y))
        return self.__kill_wumpus_tasks

    def return_map(self) -> list[list[set[TileCondition]]]:
        return self.__map


class KnowledgeBase:
    def __init__(self, position: tuple[int, int], map_width: int, map_height: int):
        #
        # POSITION
        #

        self.__position: tuple[int, int] = position
        self.__path: list[tuple[int, int]] = []

        #
        # MAP
        #

        self.__map: _Map = _Map(map_width, map_height)

    #
    # POSITION
    #

    def update_position(self, position: tuple[int, int]) -> None:
        self.__position = position
        self.__path.append(position)

    def get_path(self) -> list[tuple[int, int]]:
        return self.__path

    #
    # MAP
    #

    def return_map(self) -> list[list[set[TileCondition]]]:
        return self.__map.return_map()

    def __add_condition_if_all_surrounding_tiles_allow(self, x: int, y: int, tile_condition: TileCondition) -> bool:
        """adds (predicted) dangers if no adjacent tile disallows it"""

        # check for allowed tile_condition values
        if tile_condition not in {TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS, TileCondition.PREDICTED_PIT}:
            raise ValueError(f"Invalid value: {tile_condition}. Allowed: {TileCondition.PREDICTED_WUMPUS}, "
                             f"{TileCondition.WUMPUS}, and {TileCondition.PREDICTED_PIT}.")

        # get tile condition that the surrounding tiles have to fulfill
        if tile_condition == TileCondition.PREDICTED_PIT:
            surrounding_tiles_condition = TileCondition.BREEZE
        else:
            surrounding_tiles_condition = TileCondition.STENCH

        # check if all surrounding tiles fulfill the test condition
        count = 0
        for position in SURROUNDING_TILES:
            if self.__map.tile_has_condition(x + position[0], y + position[1], surrounding_tiles_condition):
                count += 1
                continue
            # do not have to check for walls and pits independently as they cannot be visited
            if self.__map.visited(x + position[0], y + position[1]):
                break
            count += 1
        if count == 4:
            self.__map.add_condition_to_tile(x, y, tile_condition)
            return True
        return False

    def __predict(self, x: int, y: int, tile_condition: TileCondition) -> bool:
        """predicts dangers"""

        # check for allowed tile_condition values
        if tile_condition not in {TileCondition.PREDICTED_WUMPUS, TileCondition.PREDICTED_PIT}:
            raise ValueError(f"Invalid value: {tile_condition}. Allowed: {TileCondition.PREDICTED_WUMPUS}, and "
                             f"{TileCondition.PREDICTED_PIT}.")

        # check if prediction is already made
        if self.__map.tile_has_condition(x, y, tile_condition):
            return True

        # get check parameters
        if tile_condition == TileCondition.PREDICTED_PIT:
            tile_check_1 = TileCondition.PIT
            tile_check_2 = TileCondition.WUMPUS
        else:
            tile_check_1 = TileCondition.WUMPUS
            tile_check_2 = TileCondition.PIT

        # check if knowledge is already known
        if self.__map.tile_has_condition(x, y, tile_check_1):
            return True

        # skip if prediction is not consistent
        if (self.__map.tile_has_condition(x, y, TileCondition.SAFE)
                or self.__map.tile_has_condition(x, y, TileCondition.WALL)
                or self.__map.tile_has_condition(x, y, tile_check_2)):
            return False

        # add, if consistent with surrounding tiles
        return self.__add_condition_if_all_surrounding_tiles_allow(x, y, tile_condition)

    def __add_stench_or_breeze(self, x: int, y: int, tile_condition: TileCondition) -> bool:
        """adds stenches or breezes if possible, then predicts dangers"""

        # check for allowed tile_condition values
        if tile_condition not in {TileCondition.STENCH, TileCondition.BREEZE}:
            raise ValueError(f"Invalid value: {tile_condition}. Allowed: {TileCondition.STENCH}, and "
                             f"{TileCondition.BREEZE}.")

        # check if stench or breeze is already placed
        if self.__map.tile_has_condition(x, y, tile_condition):
            return True

        # add, if not wall or pit
        if (self.__map.tile_has_condition(x, y, TileCondition.WALL)
                or self.__map.tile_has_condition(x, y, TileCondition.PIT)):
            return False
        self.__map.add_condition_to_tile(x, y, tile_condition)

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
            self.__map.remove_condition_from_tile(x, y, TileCondition.STENCH)
        elif count == 1:
            # resolve, as predicted danger is real (prediction is correct)
            for position in SURROUNDING_TILES:
                if self.__map.tile_has_condition(x + position[0], y + position[1], predicted_danger):
                    self.__map.remove_condition_from_tile(x + position[0], y + position[1], predicted_danger)
                    self.update_tile(x + position[0], y + position[1], [real_danger])
                    return True
        return True

    def __discard_and_re_predict(self, x: int, y: int, tile_condition: TileCondition) -> None:
        """discards (predicted) dangers, then re-evaluates stenches and danger predictions accordingly"""

        # check for allowed tile_condition values
        if tile_condition not in {TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS, TileCondition.PREDICTED_PIT}:
            raise ValueError(f"Invalid value: {tile_condition}. Allowed: {TileCondition.PREDICTED_WUMPUS}, "
                             f"{TileCondition.WUMPUS}, and {TileCondition.PREDICTED_PIT}.")

        if self.__map.tile_has_condition(x, y, tile_condition):
            # discard danger
            self.__map.remove_condition_from_tile(x, y, tile_condition)

            # get tile condition to re-predict
            if tile_condition == TileCondition.PREDICTED_PIT:
                prediction_condition = TileCondition.BREEZE
            else:
                prediction_condition = TileCondition.STENCH

            # (if possible) remove or re-predict surroundings
            for position in SURROUNDING_TILES:
                if self.__map.tile_has_condition(x + position[0], y + position[1], prediction_condition):
                    self.__map.remove_condition_from_tile(x + position[0], y + position[1], prediction_condition)
                    self.__add_stench_or_breeze(x + position[0], y + position[1], prediction_condition)

    def update_tile(self, x: int, y: int, tile_conditions: list[TileCondition]) -> None:
        """updates map knowledge given some knowledge about a tile"""
        # developer has to make sure that all (missing) tile conditions are listed on visit
        if (x, y) == self.__position:
            self.__map.set_visited(x, y)
            self.__map.remove_shout(x, y)

        # for every condition: check for consistency and potentially add it
        for tile_condition in tile_conditions:
            # filter already known conditions
            if self.__map.tile_has_condition(x, y, tile_condition):
                continue

            # consistency
            match tile_condition:
                case TileCondition.SAFE:
                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.SAFE)

                    # remove (predicted) dangers as the tile is safe now
                    self.__discard_and_re_predict(x, y, TileCondition.WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)
                case TileCondition.WALL:
                    # remove predicted dangers as the tile is a wall
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.WALL)
                case TileCondition.SHINY:
                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.SHINY)

                    # Shiny[x][y] => Safe[x][y]
                    self.update_tile(x, y, [TileCondition.SAFE])
                case TileCondition.WUMPUS:
                    # if tile is safe already, wumpus is already gone
                    if self.__map.tile_has_condition(x, y, TileCondition.SAFE):
                        continue

                    # remove predictions as there is a resolution now
                    self.__map.remove_condition_from_tile(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__map.remove_condition_from_tile(x, y, TileCondition.PREDICTED_PIT)

                    # add, if all surrounding tiles could be stenches
                    if self.__add_condition_if_all_surrounding_tiles_allow(x, y, TileCondition.WUMPUS):
                        # wumpus added: place stenches around wumpus
                        for position in SURROUNDING_TILES:
                            self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.STENCH)
                    else:
                        # wumpus not added: tile must be safe now
                        self.__map.add_condition_to_tile(x, y, TileCondition.SAFE)

                        # remove surrounding stenches if possible
                        for position in SURROUNDING_TILES:
                            if self.__map.tile_has_condition(x + position[0], y + position[1], TileCondition.STENCH):
                                self.__map.remove_condition_from_tile(x + position[0], y + position[1],
                                                                      TileCondition.STENCH)
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
                    self.__map.remove_condition_from_tile(x, y, TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.PIT)

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

    def get_tiles_by_condition(self, condition: TileCondition) -> set[tuple[int, int]]:
        return self.__map.get_tiles_by_condition(condition)

    def visited(self, x: int, y: int) -> bool:
        """returns whether a certain tile has been visited"""
        return self.__map.visited(x, y)

    def get_conditions_of_tile(self, x: int, y: int) -> set[TileCondition]:
        """returns all information about a tile"""
        return self.__map.get_conditions_of_tile(x, y)

    def tile_has_condition(self, x: int, y: int, tile_condition: TileCondition) -> bool:
        return self.__map.tile_has_condition(x, y, tile_condition)

    def get_closest_unvisited_tiles(self) -> set[tuple[int, int]]:
        return self.__map.get_closest_unvisited_tiles()

    def get_closest_unknown_tiles_to_any_known_tiles(self) -> set[tuple[int, int]]:
        return self.__map.get_closest_unknown_tiles_to_any_known_tiles()

    #
    # AGENTS
    #

    def add_shout(self, x: int, y: int, time: int) -> None:
        self.update_tile(x, y, [TileCondition.SAFE])
        self.__map.add_shout(x, y, time)

    def get_shouts(self) -> dict[tuple[int, int], int]:
        return self.__map.get_shouts()

    def add_kill_wumpus_task(self, x: int, y: int) -> None:
        self.__map.add_kill_wumpus_task(x, y)

    def get_kill_wumpus_tasks(self) -> set[tuple[int, int]]:
        return self.__map.get_kill_wumpus_tasks()

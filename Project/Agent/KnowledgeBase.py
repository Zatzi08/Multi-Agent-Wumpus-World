from Project.Environment.TileCondition import TileCondition


SURROUNDING_TILES = {(-1, 0), (1, 0), (0, -1), (0, 1)}


class _Map:
    def __init__(self, map_width: int, map_height: int):
        self.__map: list[list[set[TileCondition]]] = [[set() for _ in range(map_height)] for _ in range(map_width)]
        self.__visited_map: list[list[bool]] = [[False for _ in range(map_height)] for _ in range(map_width)]
        self.__tiles_by_tile_condition: list[set[tuple[int, int]]] = [set() for _ in range(len(TileCondition))]
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
        self.__closest_unknown_tiles_to_any_known_tiles.discard((x, y))

        if TileCondition.WALL in self.__map[y][x] or TileCondition.PIT in self.__map[y][x]:
            return

        for position in SURROUNDING_TILES:
            if self.__map[y + position[1]][x + position[0]]:
                continue
            self.__closest_unknown_tiles_to_any_known_tiles.add((x + position[0], y + position[1]))

    def add_condition_to_tile(self, x: int, y: int, condition: TileCondition) -> None:
        self.__map[y][x].add(condition)
        self.__tiles_by_tile_condition[condition.value].add((x, y))
        self.__update_closest_unknown_tiles_using_new_tile(x, y)
        if condition == TileCondition.WALL and (x, y) in self.__closest_unvisited_tiles:
            self.__closest_unvisited_tiles.discard((x, y))

    def tile_has_condition(self, x: int, y: int, condition: TileCondition) -> bool:
        return condition in self.__map[y][x]

    def remove_condition_from_tile(self, x: int, y: int, condition: TileCondition) -> None:
        self.__map[y][x].discard(condition)
        self.__tiles_by_tile_condition[condition.value].discard((x, y))

        if condition == TileCondition.WALL or condition == TileCondition.PIT or condition == TileCondition.SAFE:
            raise ValueError("Knowledge base is trying to remove a WALL/PIT/SAFE condition.")

    def get_conditions_of_tile(self, x: int, y: int) -> set[TileCondition]:
        return self.__map[y][x]

    def set_visited(self, x: int, y: int) -> None:
        self.__visited_map[y][x] = True
        self.__closest_unvisited_tiles.discard((x, y))
        for position in SURROUNDING_TILES:
            if (self.visited(x + position[0], y + position[1])
                    or self.tile_has_condition(x + position[0], y + position[1], TileCondition.WALL)
                    or self.tile_has_condition(x + position[0], y + position[1], TileCondition.PIT)):
                continue
            self.__closest_unvisited_tiles.add((x + position[0], y + position[1]))

    def visited(self, x: int, y: int) -> bool:
        return self.__visited_map[y][x]

    def clear_tile(self, x: int, y: int) -> None:
        self.__map[y][x].clear()

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
        if (x, y) in self.__shouts:
            del self.__shouts[(x, y)]

    def add_kill_wumpus_task(self, x: int, y: int) -> None:
        self.__kill_wumpus_tasks.add((x, y))

    def get_kill_wumpus_tasks(self) -> set[tuple[int, int]]:
        for x, y in self.__kill_wumpus_tasks.copy():
            if (TileCondition.SAFE in self.__map[y][x] or TileCondition.WALL in self.__map[y][x]
                    or TileCondition.PIT in self.__map[y][x] or TileCondition.STENCH in self.__map[y][x]):
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
        self.__surrounding_danger_count: dict[tuple[int, int, TileCondition], int] = {}
        self.__found_wumpus: set[tuple[int, int]] = set()

    #
    # POSITION
    #

    def update_position(self, position: tuple[int, int]) -> None:
        self.__position = position
        self.__path.append(position)

    def get_path(self) -> list[tuple[int, int]]:
        return self.__path

    def get_found_wumpus(self) -> set[tuple[int, int]]:
        return self.__found_wumpus
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
            # wumpus or predicted wumpus -> return if there is/was a wumpus already on surrounding tiles
            for tile in SURROUNDING_TILES:
                if (x + tile[0], y + tile[1]) in self.__found_wumpus:
                    return False
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
            if tile_condition == TileCondition.WUMPUS:
                self.__found_wumpus.add((x, y))
                for tile in SURROUNDING_TILES:
                    self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_WUMPUS)
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
            if self.__map.tile_has_condition(x, y, TileCondition.BREEZE):
                return False
            tile_check_1 = TileCondition.PIT
            tile_check_2 = TileCondition.WUMPUS
        else:
            if self.__map.tile_has_condition(x, y, TileCondition.STENCH):
                return False
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
            # remove predicted wumpus as it cannot be on stench (no 2 wumpus can be next to each other)
            self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
        else:
            predicted_danger = TileCondition.PREDICTED_PIT
            real_danger = TileCondition.PIT
            # remove predicted pit as it cannot be on breeze (no 2 pits can be next to each other)
            self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)

        # predict surrounding dangers
        self.__surrounding_danger_count[(x, y, tile_condition)] = 0
        for position in SURROUNDING_TILES:
            # count if surrounding tile could be (or is) wumpus
            if self.__predict(x + position[0], y + position[1], predicted_danger):
                self.__surrounding_danger_count[(x, y, tile_condition)] += 1
        if self.__surrounding_danger_count[(x, y, tile_condition)] == 0:
            # for breezes there cannot be 0
            if predicted_danger == TileCondition.BREEZE:
                raise ValueError(f"Knowledge base is trying to remove a breeze.")
            # for stenches: remove if 0 (stench cannot be there anymore)
            self.__map.remove_condition_from_tile(x, y, TileCondition.STENCH)
            del self.__surrounding_danger_count[(x, y, tile_condition)]
        elif self.__surrounding_danger_count[(x, y, tile_condition)] == 1:
            # resolve, as predicted danger is real (prediction is correct)
            for position in SURROUNDING_TILES:
                if self.__map.tile_has_condition(x + position[0], y + position[1], predicted_danger):
                    self.__map.remove_condition_from_tile(x + position[0], y + position[1], predicted_danger)
                    self.update_tile(x + position[0], y + position[1], {real_danger})
                    return True
        return True

    def __discard_and_re_predict(self, x: int, y: int, tile_condition: TileCondition) -> None:
        """discards (predicted) dangers, then re-evaluates stenches and danger predictions accordingly"""
        if not self.__map.tile_has_condition(x, y, tile_condition):
            return

        # check for allowed tile conditions
        if tile_condition == TileCondition.PREDICTED_PIT:
            prediction_condition: TileCondition = TileCondition.BREEZE
            predicted_danger: TileCondition = TileCondition.PREDICTED_PIT
            real_danger: TileCondition = TileCondition.PIT
        elif tile_condition == TileCondition.PREDICTED_WUMPUS or tile_condition == TileCondition.WUMPUS:
            prediction_condition: TileCondition = TileCondition.STENCH
            predicted_danger: TileCondition = TileCondition.PREDICTED_WUMPUS
            real_danger: TileCondition = TileCondition.WUMPUS
        else:
            raise ValueError(f"Invalid value: {tile_condition}. Allowed: {TileCondition.PREDICTED_WUMPUS}, "
                             f"{TileCondition.WUMPUS}, and {TileCondition.PREDICTED_PIT}.")

        # discard danger
        self.__map.remove_condition_from_tile(x, y, tile_condition)

        # (if possible) remove or re-predict surroundings
        for inner_tile in SURROUNDING_TILES:
            if self.__map.tile_has_condition(x + inner_tile[0], y + inner_tile[1], prediction_condition):
                self.__surrounding_danger_count[(x + inner_tile[0], y + inner_tile[1], prediction_condition)] -= 1
                if self.__surrounding_danger_count[(x + inner_tile[0], y + inner_tile[1], prediction_condition)] == 0:
                    if prediction_condition == TileCondition.BREEZE:
                        raise ValueError(f"Knowledge base is trying to remove a breeze.")
                    self.__map.remove_condition_from_tile(x + inner_tile[0], y + inner_tile[1], prediction_condition)
                    del self.__surrounding_danger_count[(x + inner_tile[0], y + inner_tile[1], prediction_condition)]
                elif self.__surrounding_danger_count[(x + inner_tile[0], y + inner_tile[1], prediction_condition)] == 1:
                    if prediction_condition == TileCondition.BREEZE:
                        for outer_tile in {(inner_tile[0] + tile[0], inner_tile[1] + tile[1])
                                           for tile in SURROUNDING_TILES}:
                            if self.__map.tile_has_condition(x + outer_tile[0], y + outer_tile[1],
                                                             TileCondition.PREDICTED_PIT):
                                self.__map.remove_condition_from_tile(x + outer_tile[0], y + outer_tile[1],
                                                                      TileCondition.PREDICTED_PIT)
                                self.update_tile(x + outer_tile[0], y + outer_tile[1], {TileCondition.PIT})
                    # for stenches: do not resolve predicted wumpus to wumpus based on other predicted wumpus

    def __place_stenches_or_breezes_around_danger(self, x: int, y: int, condition: TileCondition):
        match condition:
            case TileCondition.WUMPUS:
                set_condition: TileCondition = TileCondition.STENCH
            case TileCondition.PIT:
                set_condition: TileCondition = TileCondition.BREEZE
            case _:
                raise ValueError(f"Only {TileCondition.WUMPUS} and {TileCondition.PIT} are allowed.")

        for position in SURROUNDING_TILES:
            if (self.__map.tile_has_condition(x + position[0], y + position[1], TileCondition.SAFE)
                    or self.__map.visited(x + position[0], y + position[1])):
                self.__add_stench_or_breeze(x + position[0], y + position[1], set_condition)

    def update_tile(self, x: int, y: int, tile_conditions: set[TileCondition], entire_tile: bool = False)\
            -> None:
        """updates map knowledge given some knowledge about a tile"""
        conditions = list(tile_conditions)

        if entire_tile:
            if (x, y) == self.__position:
                if not self.__map.visited(x, y):
                    self.__map.set_visited(x, y)
                self.__map.remove_shout(x, y)

            if (self.__map.tile_has_condition(x, y, TileCondition.STENCH)
                    and TileCondition.STENCH not in conditions):
                self.__map.remove_condition_from_tile(x, y, TileCondition.STENCH)
                for tile in SURROUNDING_TILES:
                    self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.WUMPUS)

            if self.__map.tile_has_condition(x, y, TileCondition.SHINY) and TileCondition.SHINY not in conditions:
                self.__map.remove_condition_from_tile(x, y, TileCondition.SHINY)

        if TileCondition.SAFE in conditions:
            conditions.remove(TileCondition.SAFE)
            conditions.append(TileCondition.SAFE)

        if TileCondition.SHINY in conditions:
            conditions.remove(TileCondition.SHINY)
            conditions.append(TileCondition.SHINY)

        # for every condition: check for consistency and potentially add it
        for tile_condition in conditions:
            # filter already known conditions
            if self.__map.tile_has_condition(x, y, tile_condition):
                if tile_condition == TileCondition.SAFE:
                    if self.__map.visited(x, y) and not self.__map.tile_has_condition(x, y, TileCondition.STENCH):
                        for tile in SURROUNDING_TILES:
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_WUMPUS)
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.WUMPUS)

                    if self.__map.visited(x, y) and not self.__map.tile_has_condition(x, y, TileCondition.BREEZE):
                        for tile in SURROUNDING_TILES:
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_PIT)
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

                    if self.__map.visited(x, y) and not self.__map.tile_has_condition(x, y, TileCondition.STENCH):
                        for tile in SURROUNDING_TILES:
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_WUMPUS)
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.WUMPUS)

                    if self.__map.visited(x, y) and not self.__map.tile_has_condition(x, y, TileCondition.BREEZE):
                        for tile in SURROUNDING_TILES:
                            self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_PIT)
                case TileCondition.WALL:
                    # remove predicted dangers as the tile is a wall
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)

                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.WALL)
                case TileCondition.SHINY:
                    # add
                    self.__map.add_condition_to_tile(x, y, TileCondition.SHINY)

                    # Shiny[y][x] => Safe[y][x]
                    self.update_tile(x, y, {TileCondition.SAFE})
                case TileCondition.WUMPUS:
                    # no lying
                    self.__found_wumpus.add((x, y))
                    # if tile is safe already, wumpus is already gone
                    if self.__map.tile_has_condition(x, y, TileCondition.SAFE):
                        continue

                    # add, if all surrounding tiles could be stenches
                    if self.__add_condition_if_all_surrounding_tiles_allow(x, y, TileCondition.WUMPUS):
                        # wumpus added: place stenches around wumpus
                        self.__place_stenches_or_breezes_around_danger(x, y, TileCondition.WUMPUS)
                    else:
                        # wumpus not added: tile must be safe now
                        self.__map.add_condition_to_tile(x, y, TileCondition.SAFE)

                        # remove surrounding stenches if possible
                        for position in SURROUNDING_TILES:
                            if self.__map.tile_has_condition(x + position[0], y + position[1], TileCondition.STENCH):
                                self.__map.remove_condition_from_tile(x + position[0], y + position[1],
                                                                      TileCondition.STENCH)
                                self.__add_stench_or_breeze(x + position[0], y + position[1], TileCondition.STENCH)

                    # remove predictions as there is a resolution now
                    self.__map.remove_condition_from_tile(x, y, TileCondition.PREDICTED_WUMPUS)
                    self.__discard_and_re_predict(x, y, TileCondition.PREDICTED_PIT)
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

                    # remove predicted pits around pit (no two pits can be next to one another)
                    for tile in SURROUNDING_TILES:
                        self.__discard_and_re_predict(x + tile[0], y + tile[1], TileCondition.PREDICTED_PIT)

                    # place breezes around pit
                    self.__place_stenches_or_breezes_around_danger(x, y, TileCondition.PIT)
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
        self.update_tile(x, y, {TileCondition.SAFE})
        self.__map.add_shout(x, y, time)

    def get_shouts(self) -> dict[tuple[int, int], int]:
        return self.__map.get_shouts()

    def add_kill_wumpus_task(self, x: int, y: int) -> None:
        self.__map.add_kill_wumpus_task(x, y)

    def get_kill_wumpus_tasks(self) -> set[tuple[int, int]]:
        return self.__map.get_kill_wumpus_tasks()

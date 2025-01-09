from Project.Agent import Agent
from Project.Environment.env import EnvGenerator
from Project.Knowledge.KnowledgeBase import TileCondition


class Map:
    __slots__ = ['height', 'width', 'start_pos', 'map', 'filled_map', 'agents', 'numDeadEnds', 'info']

    def __init__(self, width, height):
        # extend grid to fit full tiles
        self.height = height
        self.width = width

        if width % 3 != 0:
            self.width += 3 - (width % 3)
        if height % 3 != 0:
            self.height += 3 - (height % 3)

        self.start_pos = (1, 1)
        gen = EnvGenerator(self.height, self.width)
        self.map = gen.getGrid()
        gen.placeWorldItems()
        self.filled_map = gen.getGrid()
        self.agents: dict[int, Agent] = {}
        self.numDeadEnds = gen.getNumDeadEnds()
        self.info = gen.info

    def add_agents(self, agents: dict[int, Agent]):
        self.agents = agents.copy()

    def get_agents(self) -> dict[int, Agent]:
        return self.agents

    def get_number_of_dead_ends(self):
        return self.numDeadEnds

    def get_tile_conditions(self, x, y):
        return self.filled_map[y][x]

    def __get_neighbors_of(self, x: int, y: int) -> list[tuple[int, int]]:
        adjacent: list[tuple[int, int]] = []
        for (xi, yi) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if TileCondition.WALL in self.filled_map[y+yi][x+xi]:
                continue
            adjacent.append((x, y))
        return adjacent

    def get_agents_in_reach(self, name: int, distance: int) -> list[int]:
        agent: Agent = self.agents[name]

        # find adjacent tiles (reachable in [distance] moves)
        x: int = agent.position[0]
        y: int = agent.position[1]
        adjacent_tiles: set[tuple[int, int]] = {(x, y)}
        current_tiles_1: set[tuple[int, int]] = {(x, y)}
        current_tiles_2: set[tuple[int, int]] = set(self.__get_neighbors_of(x, y))
        if distance <= 0:
            pass
        elif distance == 1:
            adjacent_tiles.update(current_tiles_2)
        elif distance > 1:
            adjacent_tiles.update(current_tiles_2)
            i: int = 1
            relay: bool = True
            while i < distance:
                if relay:
                    current_tiles_1.clear()
                    for (x, y) in current_tiles_2:
                        current_tiles_1.update(self.__get_neighbors_of(x, y))
                    relay = False
                    adjacent_tiles.update(current_tiles_1)
                else:
                    current_tiles_2.clear()
                    for (x, y) in current_tiles_1:
                        current_tiles_2.update(self.__get_neighbors_of(x, y))
                    relay = True
                    adjacent_tiles.update(current_tiles_2)
                i += 1

        # find adjacent agents (on adjacent tiles)
        adjacent_agents = []
        for _, agent in self.agents.items():
            if agent.position in adjacent_tiles:
                adjacent_agents.append(agent.name)
        return adjacent_agents

    def delete_condition(self, x, y, condition: TileCondition):
        self.map.filled_map[y][x].remove(condition)
        if condition in [TileCondition.WUMPUS, TileCondition.PIT]:
            if condition == TileCondition.WUMPUS:
                second_condition = TileCondition.STENCH
            else:
                second_condition = TileCondition.BREEZE
            for ox, oy in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
                self.map.filled_map.__delete_stench_or_breeze(x+ox, y+oy, second_condition)

    def __delete_stench_or_breeze(self, x, y, condition: TileCondition):
        if condition != TileCondition.STENCH and condition != TileCondition.BREEZE:
            raise "Invalid Condition"
        if condition not in self.get_tile_conditions(x, y):
            raise "Incorrect Map Initialization"
        delete = True
        for ox, oy in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
            if TileCondition.WUMPUS in self.map.filled_map[y+oy][x+ox]:
                delete = False
                break
        if delete:
            self.map.filled_map[y][x].remove(condition)

    def delete_agent(self, name):
        self.agents.pop(name)

    def get_safe_tiles(self):
        return self.info[TileCondition.SAFE]

    def print_map(self):
        EnvGenerator.printGrid(self.filled_map)

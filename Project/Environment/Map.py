from Project.Environment.env import EnvGenerator
from Project.Knowledge.KnowledgeBase import TileCondition


class Map:
    __slots__ = ['height', 'width', 'start_pos', 'map', 'filled_map', 'agents', 'numDeadEnds', 'info']

    def __init__(self, width, height, agents: list):
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
        self.agents = {}
        self.numDeadEnds = gen.getNumDeadEnds()
        self.info = gen.info
        for i in agents:
            self.agents[i.getName()] = i

    def addAgent(self, agent, spawn_position):
        if self.agents.get(agent.getName(), None) is None:
            self.agents[agent.getName()] = agent
        ADD AGENT BY SPAWN POSITION

    def getAgents(self) -> dict:
        return self.agents

    def getNumOfDeadEnds(self):
        return self.numDeadEnds

    def __getNeighbors(self, x, y):
        neighbors = []
        for xi in [-1, 0, 1]:
            for yj in [-1, 0, 1]:
                if abs(xi) == abs(yj):
                    continue
                elif 0 < x + xi < self.width and 0 < y + yj < self.height and self.map[y + yj][x + xi] is not None:
                    neighbors.append((x + xi, y + yj))
        return neighbors

    def getEventsOnTile(self, x, y):
        return self.filled_map[y][x]

    def getAgentsInReach(self, name) -> list[int]:
        agent = self.agents.get(name, None)
        if agent is None:
            raise "Invalid Name"
        adjacent = []
        x, y = agent.getPos()
        n = self.__getNeighbors(x, y) + [(x, y)]
        for i in self.agents:
            if i.getPos in n:
                adjacent.append(i.getName())
        return adjacent

    def delete_condition(self, x, y, condition: TileCondition):
        self.map.filled_map[y][x].remove(condition)
        if condition in [TileCondition.WUMPUS, TileCondition.PIT]:
            if condition == TileCondition.WUMPUS:
                second_condition = TileCondition.STENCH
            else:
                second_condition = TileCondition.BREEZE
            for ox, oy in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
                self.map.filled_map.__delete_stench_or_breeze(ox, oy, second_condition)

    def __delete_stench_or_breeze(self, x, y, condition: TileCondition):
        if condition != TileCondition.STENCH and condition != TileCondition.BREEZE:
            raise "Invalid Condition"
        if condition not in self.getEventsOnTile(x, y):
            raise "Incorrect Map Initialization"
        delete = True
        for ox, oy in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
            if TileCondition.WUMPUS in self.map.filled_map[y][x]:
                delete = False
                break
        if delete:
            self.map.filled_map[y][x].remove(condition)

    def deleteAgent(self, name):
        if self.agents.get(name, None) is not None:
            self.agents.pop(name)

    def getSafeTiles(self):
        return self.info[TileCondition.SAFE]

    def printMap(self):
        EnvGenerator.printGrid(self.filled_map)

from Project.Environment.env import EnvGenerator


class Map:
    __slots__ = ['height', 'width', 'start_pos', 'map', 'filled_map', 'agents']

    def __init__(self, width, height, agents: list):
        # extend grid to fit full tiles
        if width % 3 != 0:
            self.width += 3 - (self.width % 3)
        if height % 3 != 0:
            self.height += 3 - (self.height % 3)
        self.start_pos = (1, 1)
        gen = EnvGenerator(self.height, self.width)
        gen.genByTile()
        self.map = gen.getGrid()
        gen.placeWorldItems()
        self.filled_map = gen.getGrid()
        self.agents = {}
        for i in agents:
            self.agents[i.getName] = i

    def getNeighbors(self, x, y):
        neighbors = []
        for xi in [-1, 0, 1]:
            for yj in [-1, 0, 1]:
                if abs(xi) == abs(yj):
                    continue
                elif 0 < x + xi < self.width and 0 < y + yj < self.height and self.map[y + yj][x + xi] is not None:
                    neighbors.append((x + xi, y + yj))
        return neighbors

    def getEventsOnTile(self, x, y):
        return self.filled_map()[y][x]

    def getAgentInReach(self, x, y):
        n = self.getNeighbors(x, y) + [(x, y)]
        adjacent = []
        for i in self.agents:
            if i.getPos in n:
                adjacent.append(i)
        return adjacent

    def printMap(self):
        EnvGenerator.printGrid(self.filled_map)

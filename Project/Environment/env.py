from numpy.dtypes import StringDType

from Project.Knowledge.KnowledgeBase import TileCondition

import random

import numpy as np


class EnvGenerator:
    __slots__ = ['height', 'width', 'start_pos', 'wumpus_prob', 'pit_prob', 'treasure_prob', 'seed', 'grid',
                 'num_dead_end', 'info']

    def __init__(self, height, width, seed=42):
        self.height = height
        self.width = width
        self.start_pos = (1, 1)
        self.wumpus_prob = 0.05
        self.pit_prob = 0.03
        self.treasure_prob = 0.03
        self.seed = seed
        self.num_dead_end: int = -1
        self.grid = []
        self.info = {}
        self.__genByTile()
        self.__analyseMap()

    def getGrid(self):
        return self.grid.copy()

    def getNeighbors(self, x: int, y: int):
        neighbors = []
        for xi in [-1, 0, 1]:
            for yj in [-1, 0, 1]:
                if abs(xi) == abs(yj):
                    continue
                elif 0 < x + xi < self.width and 0 < y + yj < self.height and TileCondition.WALL not in \
                        self.grid[y + yj][x + xi]:
                    neighbors.append((x + xi, y + yj))
        return neighbors

    def __findDeadEnd(self) -> list[tuple[int, int]]:
        ends = []
        sx, sy = self.start_pos
        visit = [self.start_pos]
        visited = np.ndarray((self.width, self.height)).astype(bool)
        visited.fill(False)
        while visit:
            x, y = visit.pop()
            visited[y][x] = True
            n = self.getNeighbors(x, y)
            if len(n) == 1 and abs(x - sx) + abs(y - sy) > 1:
                ends.append((x, y))
            for xi, yi in n:
                if not visited[yi][xi]:
                    visit.append((xi, yi))
        self.num_dead_end = len(ends)
        return ends

    def __analyseMap(self):
        safe = []
        wumpus = []
        gold = []
        pit = []

        visit = [self.start_pos]
        visited = np.ndarray((self.width, self.height)).astype(bool)
        visited.fill(False)
        while visit:
            x, y = visit.pop()
            visited[y][x] = True
            n = self.getNeighbors(x, y)
            if TileCondition.WALL not in self.grid[y][x]:
                if not self.grid[y][x]:
                    safe.append((x, y))
                if TileCondition.PIT in self.grid[y][x]:
                    pit.append((x, y))
                if TileCondition.WUMPUS in self.grid[y][x]:
                    wumpus.append((x, y))
                if TileCondition.SHINY in self.grid[y][x]:
                    gold.append((x, y))

            for xi, yi in n:
                if not visited[yi][xi]:
                    visit.append((xi, yi))

        self.info[TileCondition.SAFE.value] = safe
        self.info[TileCondition.WUMPUS.value] = wumpus
        self.info[TileCondition.SHINY.value] = gold
        self.info[TileCondition.PIT.value] = pit

    def getNumDeadEnds(self):
        if self.num_dead_end == -1:
            if TileCondition.WALL not in self.grid and type(self.grid[1][1]) is list:
                self.num_dead_end = len(self.__findDeadEnd())
        return self.num_dead_end

    """
    @author: Lucas K
    @:param Array
    @:return Array.astype(int)
    [TileCondition.WALL] für Wand, [] für Weg Umwandlung zu Array
    """

    def __convertToArray(self, grid):
        g = np.ndarray((self.height, self.width), list)

        self.info[TileCondition.WALL.value] = []
        self.info["Path"] = []

        # Path = [] Wall = [TileCondition.WALL]
        for y in range(0, self.height):
            for x in range(0, self.width):
                if grid[y][x] == ' ':
                    g[y][x] = []
                    if x != 1 and y != 1:
                        self.info["Path"] += [(x, y)]
                else:
                    g[y][x] = [TileCondition.WALL]
                    self.info[TileCondition.WALL.value] += [(x, y)]
        return g

    # define Tiles -> gen grid using Tiles by prob and some rules
    def __genByTile(self):
        # Liste aller Tiles
        tiles = [np.array([["W", "W", "W"], ["W", "W", "W"], ["W", "W", "W"]]),
                 np.array([["W", "W", "W"], ["W", " ", " "], ["W", "W", "W"]]),
                 np.array([["W", "W", "W"], [" ", " ", " "], ["W", "W", "W"]]),
                 np.array([["W", "W", "W"], ["W", " ", " "], ["W", " ", "W"]]),
                 np.array([["W", "W", "W"], [" ", " ", " "], ["W", " ", "W"]]),
                 np.array([["W", " ", "W"], [" ", " ", " "], ["W", " ", "W"]]),
                 np.array([[" ", " ", " "], [" ", " ", " "], [" ", " ", " "]])]

        """
        @author: Lucas K
        @:param x, y Koordinaten in Grid
        @:return Liste an Positionen
        Gibt für eine Position alle Folgepositionen für alle Tiles und orientations aus 
        Tripel (rotation tile Exit) <- rotation counterclockwise
        """

        def directions(hor: int, ver: int):
            return [
                [
                    [],
                    [(hor + 3, ver + 0)],
                    [(hor + 3, ver + 0), (hor - 3, ver + 0)],
                    [(hor + 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)]
                ],

                [
                    [],
                    [(hor + 0, ver - 3)],
                    [(hor + 0, ver + 3), (hor + 0, ver - 3)],
                    [(hor + 3, ver + 0), (hor + 0, ver - 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)]
                ],

                [
                    [],
                    [(hor - 3, ver + 0)],
                    [(hor + 3, ver + 0), (hor - 3, ver + 0)],
                    [(hor - 3, ver + 0), (hor + 0, ver - 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)]
                ],

                [
                    [],
                    [(hor + 0, ver + 3)],
                    [(hor + 0, ver + 3), (hor + 0, ver - 3)],
                    [(hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)],
                    [(hor + 0, ver - 3), (hor + 3, ver + 0), (hor - 3, ver + 0), (hor + 0, ver + 3)]
                ]
            ]

        tile_count = 0
        blank_count = 0
        blank_ratio = 2
        random.seed(self.seed)

        tile_con = dict()
        for y_con in range(1, self.height, 3):
            for x_con in range(1, self.width, 3):
                tile_con[(x_con, y_con)] = []
                for xo, yo in directions(x_con, y_con)[0][6]:
                    if 0 < xo < self.width and 0 < yo < self.height:
                        tile_con[(x_con, y_con)].append((xo, yo))

        """
        @author: Lucas K
        @:param [TileCondition.WALL]
        @:return Leeres Array.astype(str)
        Erweitert die gegebene Höhe und Breite auf ein vielfaches von 3 
        
        @ Explanation
        Wall = [TileCondition.WALL]
        Path = [...]
        Events:
            Shine   = [..., 3, ...] = Gold
            Breeze  = [..., 9, ...]
            Stench   = [..., 6, ...]
            Pit     = [..., 7, ...]
            Wumpus  = [..., 4, ...]
        """

        def getGrid() -> np.ndarray:
            # Return Grid
            return np.ndarray((self.height, self.width)).astype(str)

        """
        @author: Lucas K
        @:param Tile_id (siehe Tiles-Liste), orientation = rotation, position (Tupel (x,y))
        @:return void
        Zum Einfügen ausgewählten Tiles in Grid 
        """

        def setTile(tile_id: int, orientation: int, pos: tuple[int, int]):
            x1, y1 = pos
            tile = np.rot90(tiles[tile_id], orientation)
            for y2 in [-1, 0, 1]:
                for x2 in [-1, 0, 1]:
                    grid[y1 + y2][x1 + x2] = tile[y2 + 1][x2 + 1]

        """
        @author: Lucas K
        @:param Position
        @:return Tile_id, orientation
        Berechnet Tile an gegebener Position und seine Position
        """

        def getPossibleTile(pos: tuple[int, int]):

            """
            @author: Lucas K
            @:param Position (x,y), connected, tile_id (siehe Tiles-List)
            @:return int rotation
            Berechnet orientation/rotation für Tile on position
            """

            def comOrientation(pos: tuple[int, int], con: list, tile_id: int):
                x, y = pos
                for o in range(0, 4):
                    ok = True
                    possible = directions(x, y)[o][tile_id]
                    for xo, yo in possible:
                        ok = ok and (0 < xo < self.width and 0 < yo < self.height)
                        if not ok:
                            break
                    if not ok:
                        continue
                    for c in con:
                        ok = ok and c in possible
                        if not ok:
                            break
                    if ok:
                        return o
                return -1

            orientation = 0
            con = tile_con[pos]
            tile = -1

            if len(con) == 4:
                p = list(range(2, 7)) + [0]
                tile, orientation = random.choice(p), 0
                if tile < 5:
                    orientation = comOrientation(pos, con, tile)
                while orientation == -1:
                    if tile == 0 and tile_count > blank_count * blank_ratio:
                        orientation = 0
                        break
                    p.remove(tile)
                    tile, orientation = random.choice(p), 0
                    orientation = comOrientation(pos, con, tile)
            elif len(con) == 3:
                p = list(range(2, 5)) + [0]
                tile, orientation = random.choice(p), 0
                if tile < 5:
                    orientation = comOrientation(pos, con, tile)
                while orientation == -1:
                    if tile == 0 and tile_count > blank_count * blank_ratio:
                        orientation = 0
                        break
                    p.remove(tile)
                    tile, orientation = random.choice(p), 0
                    orientation = comOrientation(pos, con, tile)
            elif len(con) == 2:
                p = list(range(2, 4)) + [0]
                tile, orientation = random.choice(p), 0
                orientation = comOrientation(pos, con, tile)
                while orientation == -1:
                    if tile == 0 and tile_count > blank_count * blank_ratio:
                        orientation = 0
                        break
                    p.remove(tile)
                    tile, orientation = random.choice(p), 0
                    orientation = comOrientation(pos, con, tile)
            elif len(con) == 1:
                p = list(range(0, 2))
                tile, orientation = random.choice(p), 0
                orientation = comOrientation(pos, con, tile)
                while orientation == -1:
                    if tile == 0 and tile_count > blank_count * blank_ratio:
                        orientation = 0
                        break
                    p.remove(tile)
                    tile, orientation = random.choice(p), 0
                    orientation = comOrientation(pos, con, tile)
            else:
                raise Exception("ERROR", pos, con)

            return tile, orientation

        """
        @author: Lucas K
        @:param Grid
        @:return void
        Zum debugen; füllt Grid mit den Positionen (x,y)
        """

        def fillWithPos(grid: np.ndarray):
            for y in range(0, self.height):
                for x in range(0, self.width):
                    grid[y][x] = f"({x}, {y})"

        grid = getGrid()
        #fillWithPos(grid)

        toSet = set()
        toSet.add(self.start_pos)
        seen = []
        while toSet:
            pos = toSet.pop()
            if pos in seen:
                continue
            seen.append(pos)
            # 0 = Top-Left; 1 = Bottom-Left; 2 = Bottom-Right; 3 = Top-Right
            t, o = -1, -1

            t, o = getPossibleTile(pos)
            if t != 0:
                tile_count += 1
            else:
                blank_count += 1

            if t != -1:
                setTile(t, o, pos)
                x, y = pos
                tile_con_pos = []
                for xo, yo in directions(x, y)[o][t]:
                    if 0 < xo < self.width - 1 and 0 < yo < self.height - 1:
                        toSet.add((xo, yo))
                        tile_con_pos.append((xo, yo))
                for xo, yo in set(tile_con[pos]).difference(tile_con_pos):
                    tile_con[(xo, yo)].remove(pos)
        self.grid = self.__convertToArray(grid)

    """
    @author: Lucas K
    @:param Grid
    @:return void
    Zum Platzieren von Wumpus, Pit und Gold
    """

    def placeWorldItems(self):
        if self.grid is None:
            raise Exception("No Grid defined")
        random.seed(self.seed)

        grid = self.grid.copy()

        space = self.info["Path"]

        treasure = random.sample(space, k=int(len(space) * self.treasure_prob))
        wumpus = random.sample(space, k=int(len(space) * self.wumpus_prob))
        pit = random.sample(space, k=int(len(space) * self.pit_prob))

        for tx, ty in treasure:
            grid[ty][tx].append(TileCondition.SHINY)

        for wx, wy in wumpus:
            if set(grid[wy][wx]).intersection({TileCondition.PIT, TileCondition.WUMPUS, TileCondition.SHINY, TileCondition.STENCH}):
                continue
            grid[wy][wx].append(TileCondition.WUMPUS)
            for sx, sy in self.getNeighbors(wx, wy):
                grid[sy][sx].append(TileCondition.STENCH)

        for px, py in pit:
            if set(grid[py][px]).intersection({TileCondition.PIT, TileCondition.WUMPUS, TileCondition.SHINY, TileCondition.BREEZE}):
                continue
            grid[py][px].append(TileCondition.PIT)
            for bx, by in self.getNeighbors(px, py):
                grid[by][bx].append(TileCondition.BREEZE)

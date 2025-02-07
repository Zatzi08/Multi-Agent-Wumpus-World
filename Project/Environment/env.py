from Project.Environment.TileCondition import TileCondition

import random

import numpy as np


class EnvGenerator:
    __slots__ = ['height', 'width', 'start_pos', 'wumpus_prob', 'pit_prob', 'treasure_prob', 'grid',
                 'num_dead_end', '__info']

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.start_pos = (1, 1)
        self.wumpus_prob = 0.05
        self.pit_prob = 0.03
        self.treasure_prob = 0.03
        self.num_dead_end: int = -1
        self.grid = []
        self.__info: dict = dict()
        self.__genByTile()

    def get_map_info(self):
        if 2 not in self.__info.keys():
            self.__analyseMap()
        return self.__info

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

    def __analyseMap(self):
        safe = set()
        wumpus = set()
        gold = set()
        pit = set()

        for x in range(0, self.width):
            for y in range(0, self.height):
                if TileCondition.WALL not in self.grid[y][x]:
                    if TileCondition.PIT in self.grid[y][x]:
                        pit.add((x, y))
                    elif TileCondition.WUMPUS in self.grid[y][x]:
                        wumpus.add((x, y))
                    elif TileCondition.SHINY in self.grid[y][x]:
                        gold.add((x, y))
                    elif TileCondition.STENCH not in self.grid[y][x] and TileCondition.BREEZE not in self.grid[y][x]:
                        safe.add((x, y))


        self.__info[TileCondition.SAFE.value] = safe
        self.__info[TileCondition.WUMPUS.value] = wumpus
        self.__info[TileCondition.SHINY.value] = gold
        self.__info[TileCondition.PIT.value] = pit

    def __convertToArray(self, grid):

        """
        @author: Lucas K
        @:param Array
        @:return Array.astype(int)
        [TileCondition.WALL] für Wand, [TileCondition.SAFE] für Weg Umwandlung zu Array
        """

        g = np.ndarray((self.height, self.width), list)

        wall = set()
        loca = set()

        # Path = [] Wall = [TileCondition.WALL]
        for y in range(0, self.height):
            for x in range(0, self.width):
                if grid[y][x] == ' ':
                    g[y][x] = [TileCondition.SAFE]
                    if x != 1 and y != 1:
                        loca.add((x, y))
                else:
                    g[y][x] = [TileCondition.WALL]
                    wall.add((x, y))
        self.__info["locations"] = loca
        self.__info[TileCondition.WALL.value] = wall
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

        def __directions(hor: int, ver: int):

            """
            @author: Lucas K
            @:param x, y Koordinaten in Grid
            @:return Liste an Positionen
            Gibt für eine Position alle Folgepositionen für alle Tiles und orientations aus
            Tripel (rotation tile Exit) <- rotation counterclockwise
            """

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

        tile_con = dict()
        for y_con in range(1, self.height, 3):
            for x_con in range(1, self.width, 3):
                tile_con[(x_con, y_con)] = []
                for xo, yo in __directions(x_con, y_con)[0][6]:
                    if 0 < xo < self.width and 0 < yo < self.height:
                        tile_con[(x_con, y_con)].append((xo, yo))

        def __getGrid() -> np.ndarray:
            # Return Grid
            return np.ndarray((self.height, self.width)).astype(str)

        def setTile(tile_id: int, orientation: int, pos: tuple[int, int]):

            """
            @author: Lucas K
            @:param Tile_id (siehe Tiles-Liste), orientation = rotation, position (Tupel (x,y))
            @:return void
            Zum Einfügen ausgewählten Tiles in Grid
            """

            x1, y1 = pos
            tile = np.rot90(tiles[tile_id], orientation)
            for y2 in [-1, 0, 1]:
                for x2 in [-1, 0, 1]:
                    grid[y1 + y2][x1 + x2] = tile[y2 + 1][x2 + 1]

        def getPossibleTile(pos: tuple[int, int]):

            """
            @author: Lucas K
            @:param Position (x, y)
            @:return Tile_id, orientation
            Berechnet Tile an gegebener Position und seine Position
            """

            def comOrientation(pos: tuple[int, int], con: list, tile_id: int):

                """
                @author: Lucas K
                @:param Position (x,y), connected, tile_id (siehe Tiles-List)
                @:return int rotation
                Berechnet orientation/rotation für Tile on position
                """

                x, y = pos
                for o in range(0, 4):
                    ok = True
                    possible = __directions(x, y)[o][tile_id]
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

        def fillWithPos(grid: np.ndarray):
            """
            @author: Lucas K
            @:param ndarray
            @:return void
            Zum debugen; füllt Grid mit den Positionen (x,y)
            """
            for y in range(0, self.height):
                for x in range(0, self.width):
                    grid[y][x] = f"({x}, {y})"

        grid = __getGrid()
        # fillWithPos(grid)

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
                for xo, yo in __directions(x, y)[o][t]:
                    if 0 < xo < self.width - 1 and 0 < yo < self.height - 1:
                        toSet.add((xo, yo))
                        tile_con_pos.append((xo, yo))
                for xo, yo in set(tile_con[pos]).difference(tile_con_pos):
                    tile_con[(xo, yo)].remove(pos)
        self.grid = self.__convertToArray(grid)

    def placeWorldItems(self):

        """
        @author: Lucas K
        @:return void
        Zum Platzieren von Wumpus, Pit und Gold
        """

        if self.grid is None:
            raise Exception("No Grid defined")

        grid = self.grid.copy()

        space = sorted(self.__info["locations"])

        treasure = random.sample(space, k=int(len(space) * self.treasure_prob))
        wumpus = random.sample(space, k=int(len(space) * self.wumpus_prob))
        pit = random.sample(space, k=int(len(space) * self.pit_prob))

        for tx, ty in treasure:
            grid[ty][tx].append(TileCondition.SHINY)

        for wx, wy in wumpus:
            if set(grid[wy][wx]).intersection(
                    {TileCondition.PIT, TileCondition.WUMPUS, TileCondition.SHINY, TileCondition.STENCH}):
                continue
            grid[wy][wx].remove(TileCondition.SAFE)
            grid[wy][wx].append(TileCondition.WUMPUS)
            for sx, sy in self.getNeighbors(wx, wy):
                if TileCondition.PIT not in grid[sy][sx]:
                    grid[sy][sx].append(TileCondition.STENCH)

        for px, py in pit:
            if set(grid[py][px]).intersection(
                    {TileCondition.PIT, TileCondition.WUMPUS, TileCondition.SHINY, TileCondition.BREEZE, TileCondition.STENCH}):
                continue
            grid[py][px].remove(TileCondition.SAFE)
            grid[py][px].append(TileCondition.PIT)
            for bx, by in self.getNeighbors(px, py):
                grid[by][bx].append(TileCondition.BREEZE)

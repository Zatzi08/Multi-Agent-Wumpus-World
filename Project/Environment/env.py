from Project.Knowledge.KnowledgeBase import TileCondition

import random

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors

import datetime


class EnvGenerator:
    __slots__ = ['height', 'width', 'start_pos', 'wumpus_prob', 'pit_prob', 'treasure_prob', 'seed', 'grid',
                 'room_list']

    def __init__(self, height, width, seed=42):
        self.height = height
        self.width = width
        self.start_pos = (1, 1)
        self.wumpus_prob = 0.5
        self.pit_prob = 0.3
        self.treasure_prob = 0.3
        self.seed = seed
        self.grid = None
        self.room_list = []

    def getGrid(self):
        return self.grid.copy()

    """
    @author: Lucas K
    @:param Array
    @:return Array.astype(int)
    None für Wand, [] für Weg Umwandlung zu Array
    """

    def convert_to_Array(self, grid):
        g = np.ndarray((self.height, self.width), list)
        # Path = [] Wall = None
        for y in range(0, self.height):
            for x in range(0, self.width):
                if grid[y][x] == ' ':
                    g[y][x] = []
                else:
                    g[y][x] = None
        return g

    # define Tiles -> gen grid using Tiles by prob and some rules
    def genByTile(self):
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
        @:param None
        @:return Leeres Array.astype(str)
        Erweitert die gegebene Höhe und Breite auf ein vielfaches von 3 
        
        @ Explanation
        Wall = None
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

            if t == 6:
                self.room_list.append(pos)

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

        self.grid = self.convert_to_Array(grid)

    """
    @author: Lucas K
    @:return void
    Zum speichern des Grid als png
    """

    def printGrid(self):

        def convert_to_int(grid):
            g = np.ndarray((self.height, self.width), int)

            for y in range(0, self.height):
                for x in range(0, self.width):
                    # Wall
                    if grid[y][x] is None:
                        g[y][x] = 0
                    # Wumpus
                    elif TileCondition.WUMPUS in grid[y][x]:
                        g[y][x] = 40
                    # Gold
                    elif TileCondition.SHINY in grid[y][x]:
                        g[y][x] = 20
                    # Pit
                    elif TileCondition.PIT in grid[y][x]:
                        g[y][x] = 30
                    # Path
                    else:
                        g[y][x] = 10
            return g

        data = convert_to_int(self.grid)
        print("PRINTING!", datetime.datetime.now())
        cmap = colors.ListedColormap(['black', 'white', 'yellow', 'blue', 'red'])
        bounds = [0, 10, 20, 30, 40, 50]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        plt.figure(figsize=(self.width, self.height))
        plt.pcolor(data[::-1], cmap=cmap, norm=norm, edgecolors='k', linewidths=3)
        plt.savefig("fig")
        print("PRINTED", datetime.datetime.now())

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

        def getNeighbors(x: int, y: int):
            neighbors = []
            for xi in [-1, 0, 1]:
                for yj in [-1, 0, 1]:
                    if abs(xi) == abs(yj):
                        continue
                    elif 0 < x + xi < self.width and 0 < y + yj < self.height and grid[y + yj][x + xi] is not None:
                        neighbors.append((x + xi, y + yj))
            return neighbors

        def find_dead_end() -> list[tuple[int, int]]:
            ends = []
            sx, sy = self.start_pos
            visit = [self.start_pos]
            visited = np.ndarray((self.width, self.height)).astype(bool)
            visited.fill(False)
            while visit:
                x, y = visit.pop()
                visited[y][x] = True
                n = getNeighbors(x, y)
                if len(n) == 1 and abs(x - sx) + abs(y - sy) > 1:
                    ends.append((x, y))
                for xi, yi in n:
                    if not visited[yi][xi]:
                        visit.append((xi, yi))
            return ends

        dead = find_dead_end()

        treasure = random.sample(dead, k=int(len(dead) * self.treasure_prob))
        treasure_Wumpus = random.sample(treasure, k=int(len(treasure) * self.wumpus_prob))
        pit_room = random.sample(self.room_list, k=int(len(self.room_list) * self.pit_prob))
        room_without_pit = list(set(self.room_list).difference(set(pit_room)))
        wumpus_room = random.sample(room_without_pit, k=int(len(room_without_pit) * self.wumpus_prob))

        for tx, ty in treasure:
            grid[ty][tx].append(TileCondition.SHINY)

        for tx, ty in treasure_Wumpus:
            nei = getNeighbors(tx, ty)
            x, y = random.choices(nei, k=1)[0]
            grid[y][x].append(TileCondition.WUMPUS)
            for sx, sy in getNeighbors(x, y):
                grid[sy][sx].append(TileCondition.STENCH)

        for wx, wy in wumpus_room:
            x, y = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1), (0, 0)])
            grid[wy + y][wx + x].append(TileCondition.WUMPUS)
            for sx, sy in getNeighbors(wx + x, wy + y):
                grid[sy][sx].append(TileCondition.STENCH)

        for px, py in pit_room:
            x, y = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1), (0, 0)])
            grid[py + y][px + x].append(TileCondition.PIT)
            for bx, by in getNeighbors(px + x, py + y):
                grid[by][bx].append(TileCondition.BREEZE)


a = EnvGenerator(120, 120, 42)
a.genByTile()
a.placeWorldItems()
a.printGrid()

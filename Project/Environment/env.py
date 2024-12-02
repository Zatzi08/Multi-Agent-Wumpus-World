import math
import random

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors

import datetime


class EnvGenerator:
    __slots__ = ['height', 'width', 'start_pos', 'gold_count', 'wumpus_prob', 'pit_prob', 'seed', 'grid']

    def __init__(self, height, width, seed=42):
        self.height = height
        self.width = width
        self.start_pos = (1, 1)
        self.gold_count = math.sqrt((height * width))
        self.wumpus_prob = 0.5
        self.pit_prob = 0.01
        self.seed = seed
        self.grid = None

    def getGrid(self):
        return self.grid

    """
    @author: Lucas K
    @:param Array (zukünftiges Grid)
    @:return void
    Zur visuellen Ausgabe des Grids in der Konsole
    """

    def print_grid(self, grid: np.ndarray):
        f = open("grid.txt", 'w', encoding='UTF-8')
        for y in range(0, self.height):
            line = ""
            for x in range(0, self.width):
                if grid[y][x] == ' ':
                    line += " "
                else:
                    line += "■  "
            f.write(line + "\n")

    """
    @author: Lucas K
    @:param Array
    @:return Array.astype(int)
    1 für Wand, 0 für Weg Umwandlung zu int
    """

    def convert_to_int(self, grid):
        g = np.ndarray((self.height, self.width))
        g.astype(int)

        for y in range(0, self.height):
            for x in range(0, self.width):
                if grid[y][x] == ' ':
                    g[y][x] = 0
                else:
                    g[y][x] = 1
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
        """

        def getGrid() -> np.ndarray:
            # extend grid to fit full tiles
            if self.width % 3 != 0:
                self.width += 3 - (self.width % 3)
            if self.height % 3 != 0:
                self.height += 3 - (self.height % 3)
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
        fillWithPos(grid)

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

        self.grid = self.convert_to_int(grid)

    """
    @author: Lucas K
    @:param Grid
    @:return void
    Zum platzieren von Wumpus, Pit und Gold
    """

    def printGrid(self):
        print("PRINTING!", datetime.datetime.now())
        cmap = colors.ListedColormap(['black', 'white'])
        plt.figure(figsize=(self.width, self.height))
        plt.pcolor(self.grid[::-1], cmap=cmap, edgecolors='k', linewidths=3)
        plt.savefig("fig")
        print("PRINTED", datetime.datetime.now())

    def placeWorldItems(self):
        if self.grid is None:
            raise Exception("No Grid defined")
        pass

    # --------------------------------------------------------------------------------------------------------- #
    # Every other tile (both dim) is wall -> set other walls by random with prob p_w
    def genByRandom(self):
        pass


a = EnvGenerator(300, 300, 123)
a.genByTile()
a.getGrid()

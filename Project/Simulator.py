import Environment.env

a = Environment.env.EnvGenerator(120, 120, 123)
a.genByTile()
Map = a.getGrid()


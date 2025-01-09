from Project.Environment.Map import Map

import random

random.seed()
PLAYINGFIELD = Map(int(input("height of Grid\n")), int(input("width of Grid\n")), [])

for i in range(int(input("Anzahl an Agenten\n"))):
    pass
    r = random.choice("Hunter", "Kartograf", ...)
    pos = random.choice(PLAYINGFIELD.getSafeTiles())
    match r:
        case "Hunter":
            PLAYINGFIELD.addAgent(base_agent(name, ...))
    #PLAYINGFIELD.addAgent()


for agent in PLAYINGFIELD.getAgents():
    pass
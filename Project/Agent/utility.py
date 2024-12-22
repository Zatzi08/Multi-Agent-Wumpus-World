import numpy as np
from Project.Knowledge import KnowledgeBase
from Project import Agent
from Project.Knowledge.KnowledgeBase import TileCondition


#Überlegungen:
#     UNKNOWN: 0
#     SAFE: 1
#     WALL: 2
#     SHINY: 3
#     WUMPUS: 4
#     PREDICTED_WUMPUS: 5
#     STENCH: 6
#     PIT: 7
#     PREDICTED_PIT: 8
#     BREEZE: 9
#Ziel = Wumpus
#--> Ranking der Felder: 4 5 6 3 0 1 9 8 7=2
#Ziel = Gold
# --> Ranking der Felder: 3 0 1 6=9 5=8 4=7=2
# Ziel = Map
# --> Ranking der Felder: 0 1 3 6=9 5=8 4=7=2
# Ziel = Gold, Wumpus
# --> Ranking der Felder: 3=4 5 6 0 1 9 8 2=7

# TODO: rename type(agent) sobald Agenten eigene Dateien haben

def goals_to_field_value(goals):
    field_utility: dict = {}
    max_utility = 200
    if "wumpus" in goals and "gold" in goals:
        ranks = 6
        field_utility[4] = max_utility
        field_utility[3] = max_utility
        field_utility[5] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[0] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[8] = max_utility - ranks * float(max_utility / ranks)
        field_utility[2] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[7] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "wumpus" in goals:
        ranks = 7
        field_utility[4] = max_utility
        field_utility[5] = max_utility - (ranks - 6) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[3] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[0] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[8] = max_utility - ranks * float(max_utility / ranks)
        field_utility[2] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[7] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "gold" in goals:
        ranks = 4
        field_utility[3] = max_utility
        field_utility[0] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[5] = max_utility - ranks * float(max_utility / ranks)
        field_utility[8] = max_utility - ranks * float(max_utility / ranks)
        field_utility[4] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[2] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[7] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "map" in goals:
        ranks = 4
        field_utility[0] = max_utility
        field_utility[1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[3] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[5] = max_utility - ranks * float(max_utility / ranks)
        field_utility[8] = max_utility - ranks * float(max_utility / ranks)
        field_utility[4] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[2] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[7] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

def risky_tile(pos_x, pos_y, agent, map_knowledge, tile_states):
    avoid_tiles = [2, 4, 5, 7, 8]
    if type(agent) is "Project.Agent.base_agent.knight" and agent.health > 1:
        avoid_tiles.remove(4)
        avoid_tiles.remove(5)
    elif type(agent) is "Project.Agent.base_agent.hunter"
    for state in tile_states:
        if (pos_x, pos_y, state) in map_knowledge.__map:
            return True
    return False

#EdgeCases:
# Hunter will nicht auf PotentialWumpus
# low health swordsman will nicht auf PotentialWumpus
#
def a_search(map_knowledge: KnowledgeBase, end, field_utility, agent):
    def heuristik(pos_x, pos_y, end, steps):
        end_x, end_y = end
        return abs(pos_x - end_x) + abs(pos_y - end_y) + steps

    start_x, start_y = map_knowledge.__position
    pos_x, pos_y = map_knowledge.__position
    queue = []
    steps = 1

    if (start_x, start_y) == end:
        return "", -1

    #Struktur vom Eintrag: [heuristik, x,y,next_move]
    neighbours = [[pos_x + x, pos_y + y, move] for x, y, move in
                  [[0, 1, "up"], [1, 0, "right"], [0, -1, "down"], [-1, 0, "left"]]]

    avoid_tiles = [2, 4, 5, 7, 8]
    if type(agent) is "Project.Agent.base_agent.knight" and agent.health > 1:
        avoid_tiles.remove(4)
        avoid_tiles.remove(5)
    elif type(agent) is "Project.Agent.base_agent.knight": #TODO: function to get arrow amount
        if agent.items[1,2] > 0: avoid_tiles.remove(4)
    for x, y, move in neighbours:
        if risky_tile(x,y,agent, map_knowledge,avoid_tiles):
            neighbours.remove([x, y, move])

    new_field = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
    queue += new_field
    queue.sort(key=lambda x: -x[0])
    pos = queue.pop()
    steps += 1

    # pos: [heuristik, x,y,next_move]
    while (pos[1], pos[2]) != end:
        #get and insert neighbours of pos in queue
        neighbours = [[pos[1] + x, pos[2] + y, pos[3]] for x, y in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
        new_field = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
        queue += new_field
        queue.sort(key=lambda x: -x[0])
        #get next pos
        pos = queue.pop()
        while risky_tile(pos[1],pos[2],agent,map_knowledge,avoid_tiles) and len(queue) > 0:
            pos = queue.pop()
        if len(queue) == 0 and risky_tile(pos[1],pos[2],agent,map_knowledge,avoid_tiles): # no path found
            return "", -1
        steps += 1

    next_move = pos[3]
    condition = 0
    utility = field_utility[map_knowledge[pos[1]][pos[2]]] / pos[0]  #Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
    return next_move, utility


def utility_movement(map_knowledge: KnowledgeBase, agent):
    field_utility = goals_to_field_value(agent.goal)
    best_utility = {"right": -1, "left": -1, "up": -1, "down": -1}
    max_utility = 0
    next_move = "stay"
    avoid_tiles = [2, 4, 5, 7, 8] # wall, wumpus, potential wumpus, pit, potential pit
    if type(agent) is "Project.Agent.base_agent.knight" or type(agent) is "Project.Agent.base_agent.hunter":
        avoid_tiles.remove(4)
        avoid_tiles.remove(5)
    for pos in map_knowledge.__tile_exists:
        pos_x, pos_y = pos
        if risky_tile(pos_x,pos_y,agent,map_knowledge,avoid_tiles): # skip undesired tiles
            continue
        move, utility = a_search(map_knowledge, pos, field_utility, agent)
        if utility > best_utility[move]:
            best_utility[move] = utility
        if utility > max_utility:
            next_move = move
    return best_utility, next_move


#Überlegungen:
# Information:
#   Kartograf will jeglichen Informationsaustausch
#   Knight will
# if cfp für Informationsaustausch:
#       goal = map -->
# TODO: Wie wäre es mit Nutzen der Kommunikation ist gleich Nutzen der bekommenden Info/Dienstleistung - Nutzen gegebener Info/Dienstleistung (Nutzen ist ja ähnlich zu Wert)
def utility_communication():

    pass

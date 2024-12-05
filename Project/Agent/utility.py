import numpy as np
from Project.Knowledge import KnowledgeBase
from Project import Agent


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

#TODO: rename type(agent) sobald agenten eigene Dateien haben
def role_to_goals(agent):
    match type(agent):
        case "Cartographer":
            return ["map"]
        case "Cartographer":
            return ["gold"]
        case "Cartographer":
            return ["gold", "wumpus"]
        case "Cartographer":
            return ["wumpus"]


def goals_to_field_value(goals):
    field_utility: dict = {}
    max_utility = 50
    if "wumpus" in goals and "gold" in goals:
        ranks = 7
        field_utility[4] = max_utility
        field_utility[3] = max_utility
        field_utility[5] = max_utility - (ranks - 6) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[0] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[8] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[2] = max_utility - ranks * float(max_utility / ranks)
        field_utility[7] = max_utility - ranks * float(max_utility / ranks)
        return field_utility

    if "wumpus" in goals:
        ranks = 8
        field_utility[4] = max_utility
        field_utility[5] = max_utility - (ranks - 7) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 6) * float(max_utility / ranks)
        field_utility[3] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[0] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[8] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[2] = max_utility - ranks * float(max_utility / ranks)
        field_utility[7] = max_utility - ranks * float(max_utility / ranks)
        return field_utility

    if "gold" in goals:
        ranks = 5
        field_utility[3] = max_utility
        field_utility[0] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[5] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[8] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[4] = max_utility - ranks * float(max_utility / ranks)
        field_utility[2] = max_utility - ranks * float(max_utility / ranks)
        field_utility[7] = max_utility - ranks * float(max_utility / ranks)
        return field_utility

    if "map" in goals:
        ranks = 5
        field_utility[0] = max_utility
        field_utility[1] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[3] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[6] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[9] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[5] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[8] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[4] = max_utility - ranks * float(max_utility / ranks)
        field_utility[2] = max_utility - ranks * float(max_utility / ranks)
        field_utility[7] = max_utility - ranks * float(max_utility / ranks)
        return field_utility


def a_search(map_knowledge: KnowledgeBase, end, field_utility,agent):
    def heuristik(pos_x, pos_y, end_x, end_y, steps):
        return abs(pos_x - end_x) + abs(pos_y - end_y) + steps

    start_x, start_y = map_knowledge.__position
    end_x, end_y = end
    pos_x, pos_y = (start_x, start_y)
    queue = []
    steps = 0

    if (start_x, start_y) == end:
        return "", -1

    #Struktur vom Eintrag: [heuristik, x,y,next_move]
    neighbours = [[pos_x + x, pos_y + y, move] for x, y, move in
                  [[0, 1, "up"], [1, 0, "right"], [0, -1, "down"], [-1, 0, "left"]]]
    #Hunter: potential wumpus hat hohe utility, aber  will nicht auf ein potential wumpus feld gehen (stirbt maybe)
    if type(agent) == 'Project.Agent.base_agent.hunter':
        for x,y,move in neighbours:
            if

    new_field = [[heuristik(x, y, end_x, end_y, steps), x, y, move] for x, y, move in neighbours]
    queue += new_field
    queue.sort(key=lambda x: -x[0])
    pos = queue.pop()
    steps += 1
    # pos: [heuristik, x,y,next_move]
    while pos[1] != end_x and pos[2] != end_y:
        #get and insert neighbours of pos
        neighbours = [[pos[1] + x, pos[2] + y, pos[3]] for x, y in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
        new_field = [[heuristik(x, y, end_x, end_y, steps), x, y, move] for x, y, move in neighbours]
        queue += new_field
        queue.sort(key=lambda x: -x[0])
        #get next pos
        pos = queue.pop()
        condition = 0  #unknown
        for x, y, state in map_knowledge.map:
            if pos[1] == x and pos[2] == y:
                condition = state
                break
        while field_utility[condition] == 0:  #nicht über "Game Over"-Feld gehen
            pos = queue.pop()
            for x, y, state in map_knowledge.map:
                if pos[1] == x and pos[2] == y:
                    condition = state
                    break
        steps += 1

    next_move = pos[3]
    utility = field_utility[map_knowledge[pos[1]][pos[2]]] / pos[
        0]  #Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
    return next_move, utility


#TODO: Agentenrollen integrieren z.B. Hunter will nicht auf (potential) Wumpus aber Knight schon
def utility_movement(map_knowledge: KnowledgeBase, agent):
    field_utility = goals_to_field_value(role_to_goals(agent))
    best_utility = {"right": -1, "left": -1, "up": -1, "down": -1}
    max_utility = 0
    next_move = "stay"
    for pos in map_knowledge.__tile_exists:
        move, utility = a_search(map_knowledge, pos, field_utility)
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
def utility_communication():
    pass

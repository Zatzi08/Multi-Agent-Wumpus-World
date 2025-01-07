from Project.Knowledge import KnowledgeBase
from Project.communication.protocol import Message
from Project.communication.protocol import Performative
from Project.Knowledge.KnowledgeBase import TileCondition
import heapq


#Überlegungen:
#     UNKNOWN: -1
#     SAFE: 0
#     WALL: 1
#     SHINY: 2
#     WUMPUS: 3
#     PREDICTED_WUMPUS: 4
#     STENCH: 5
#     PIT: 6
#     PREDICTED_PIT: 7
#     BREEZE: 8
#Ziel = Wumpus
#--> Ranking der Felder: 4 5 6 3 0 1 9 8 7=2 (-1)
#Ziel = Gold
# --> Ranking der Felder: 3 0 1 6=9 5=8 4=7=2 (-1)
# Ziel = Map
# --> Ranking der Felder: 0 1 3 6=9 5=8 4=7=2 (-1)
# Ziel = Gold, Wumpus
# --> Ranking der Felder: 3=4 5 6 0 1 9 8 2=7 (-1)

# TODO: rename type(agent) sobald Agenten eigene Dateien haben

def goals_to_field_value(goals):
    field_utility: dict = {}
    max_utility = 200
    if "wumpus" in goals and "gold" in goals:
        ranks = 6
        field_utility[TileCondition.WUMPUS] = max_utility
        field_utility[TileCondition.SHINY] = max_utility
        field_utility[TileCondition.PREDICTED_WUMPUS] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[TileCondition.STENCH] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[-1] = max_utility - (ranks - 3) * float(max_utility / ranks) #unknown
        field_utility[TileCondition.SAFE] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[TileCondition.BREEZE] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_PIT] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.PIT] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.WALL] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "wumpus" in goals:
        ranks = 7
        field_utility[TileCondition.WUMPUS] = max_utility
        field_utility[TileCondition.PREDICTED_WUMPUS] = max_utility - (ranks - 6) * float(max_utility / ranks)
        field_utility[TileCondition.STENCH] = max_utility - (ranks - 5) * float(max_utility / ranks)
        field_utility[TileCondition.SHINY] = max_utility - (ranks - 4) * float(max_utility / ranks)
        field_utility[-1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[TileCondition.SAFE] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[TileCondition.BREEZE] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_PIT] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.PIT] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.WALL] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "gold" in goals:
        ranks = 4
        field_utility[TileCondition.SHINY] = max_utility
        field_utility[-1] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[TileCondition.SAFE] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[TileCondition.STENCH] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.BREEZE] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_WUMPUS] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_PIT] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.WUMPUS] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.PIT] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.WALL] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility

    if "map" in goals:
        ranks = 4
        field_utility[-1] = max_utility
        field_utility[TileCondition.SAFE] = max_utility - (ranks - 3) * float(max_utility / ranks)
        field_utility[TileCondition.SHINY] = max_utility - (ranks - 2) * float(max_utility / ranks)
        field_utility[TileCondition.STENCH] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.BREEZE] = max_utility - (ranks - 1) * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_PIT] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.PREDICTED_WUMPUS] = max_utility - ranks * float(max_utility / ranks)
        field_utility[TileCondition.WUMPUS] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.PIT] = max_utility - (ranks + 1) * float(max_utility / ranks)
        field_utility[TileCondition.WALL] = max_utility - (ranks + 1) * float(max_utility / ranks)
        return field_utility


def risky_tile(pos_x, pos_y, agent, map_knowledge, tile_states):
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


    if map_knowledge.__position == end:
        return "", -1

    pos_x, pos_y = map_knowledge.__position
    queue = []
    steps = 1
    #TODO: ist eigene Map ein Torus? Wenn nein, implementiere Boarders bei Nachbarn
    neighbours = [[pos_x + x, pos_y + y, move] for x, y, move in
                  [[0, 1, "up"], [1, 0, "right"], [0, -1, "down"], [-1, 0, "left"]]]

    #avoid certain tiles if its a direct neighbour
    avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
    if type(agent) is "Project.Agent.base_agent.knight" and agent.health > 1:
        avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
        avoid_tiles.remove(TileCondition.WUMPUS)
    for x, y, move in neighbours:
        if risky_tile(x,y,agent, map_knowledge, avoid_tiles):
            neighbours.remove([x, y, move])

    new_field = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
    queue += new_field
    heapq.heapify(queue)
    pos = heapq.heappop(queue)
    steps += 1

    # pos: [heuristik, x,y,next_move]
    while (pos[1], pos[2]) != end:
        #get and insert neighbours of pos in queue
        neighbours = [[pos[1] + x, pos[2] + y, pos[3]] for x, y in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
        new_field = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
        for tile in new_field:
            heapq.heappush(queue, tile)

        #get next pos
        pos = heapq.heappop(queue)

        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
        #different avoid tiles as soon as its not a direct neighbor of position
        if (type(agent) is "Project.Agent.base_agent.knight" and agent.health > 1) or steps > 10:
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        elif type(agent) is "Project.Agent.base_agent.hunter":
            #zweites if-Statement notwendig, da andere Rollen am Index [0][1] kein Inhalt haben
            if agent.items[0][1] > 0 or steps > 10:
                avoid_tiles.remove(TileCondition.WUMPUS)
        while risky_tile(pos[1],pos[2],agent,map_knowledge,avoid_tiles) and len(queue) > 0:
            pos = heapq.heappop(queue)
        if len(queue) == 0 and risky_tile(pos[1],pos[2],agent,map_knowledge,avoid_tiles): # no path found
            return "", -1
        steps += 1


    next_move = pos[3]
    states = []
    #TODO: Umgang mit mehrfachen Condition pro tile
    for state in TileCondition:
        if (pos[1],pos[2],state) in map_knowledge.__map:
            states.append(state)
    utility = field_utility[map_knowledge[pos[1]][pos[2]]] / pos[0]  #Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
    return next_move, utility


def utility_movement(map_knowledge: KnowledgeBase, agent):
    field_utility = goals_to_field_value(agent.goal)
    best_utility = {"right": -1, "left": -1, "up": -1, "down": -1}
    max_utility = 0
    next_move = "stay"
    avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
    if type(agent) is "Project.Agent.base_agent.knight" or type(agent) is "Project.Agent.base_agent.hunter":
        avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
        avoid_tiles.remove(TileCondition.WUMPUS)
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
# cfp:
# 1.Fall: Informationsaustausch
#
# 2.Fall: Wumpus töten
#   if goal != Wumpus --> Kommunikation abbrechen
#   if goal == Wumpus --> accept
# if cfp für Informationsaustausch:
#       goal = map -->
# Frage: Wie ermittelt ein Agent die Menge an Information, die er am meisten bekommen möchte
# --> nur nach Typen fragen können?
# -->  alle unbekannte Felder nennen
# --> alle unbekkannten Felder im Umkreis x

# TODO: Wie wäre es mit Nutzen der Kommunikation ist gleich Nutzen der bekommenden Info/Dienstleistung - Nutzen gegebener Info/Dienstleistung (Nutzen ist ja ähnlich zu Wert)
def utility_information(fields):
    amount = len(fields)

    pass
def utility_communication(message : Message, agent):
    if message.performative == Performative.CFP: #only for wumpus killing
        if type(agent) not in ["Project.Agent.base_agent.knight","Project.Agent.base_agent.hunter"]:
            return 0 #decline
        else:
            return 1 #accept
    if message.performative == Performative.INFORMATION:



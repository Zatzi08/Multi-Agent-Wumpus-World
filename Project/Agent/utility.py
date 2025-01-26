from Project.Agent import KnowledgeBase
from Project.Communication.protocol import RequestTypeObj
from Project.Agent.KnowledgeBase import TileCondition
from Project.Agent.Agent import AgentGoal
import heapq
from Project.Simulator import MAP_WIDTH, MAP_HEIGHT

# Überlegungen:
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
# Ziel = Wumpus
# --> Ranking der Felder: 4 5 6 3 0 1 9 8 7=2 (-1)
# Ziel = Gold
# --> Ranking der Felder: 3 0 1 6=9 5=8 4=7=2 (-1)
# Ziel = Map
# --> Ranking der Felder: 0 1 3 6=9 5=8 4=7=2 (-1)
# Ziel = Gold, Wumpus
# --> Ranking der Felder: 3=4 5 6 0 1 9 8 2=7 (-1)



def goals_to_field_value(goals):
    field_utility: dict = {}
    max_utility = 200
    if AgentGoal.WUMPUS in goals and AgentGoal.GOLD in goals:
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

    if AgentGoal.WUMPUS in goals:
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

    if AgentGoal.GOLD in goals:
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

    if AgentGoal.MAP_PROGRESS in goals:
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


def risky_tile(pos_x, pos_y, map_knowledge, tile_states):
    for state in tile_states:
        if state in map_knowledge.get_tile(pos_x, pos_y):
            return True
    return False

# EdgeCases:
# Hunter will nicht auf PotentialWumpus
# low health swordsman will nicht auf PotentialWumpus
#


def a_search(map_knowledge: KnowledgeBase, end, field_utility, agent):

    def heuristik(pos_x, pos_y, end, steps):
        end_x, end_y = end
        return abs(pos_x - end_x) + abs(pos_y - end_y) + steps


    pos_x, pos_y = map_knowledge.get_position()
    #Abbruchbedingung: already on end-field
    if (pos_x,pos_y) == end:
        return "", -1

    steps = 1
    neighbours = [[pos_x + x, pos_y + y, move] for x, y, move in
                  [[0, 1, "up"], [1, 0, "right"], [0, -1, "down"], [-1, 0, "left"]]]

    #avoid certain tiles if it's a direct neighbour
    avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
    if type(agent) is "Project.Agent.base_agent.knight" and agent.health > 1:
        avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
        avoid_tiles.remove(TileCondition.WUMPUS)
    for x, y, move in neighbours:
        if risky_tile(x,y, map_knowledge, avoid_tiles):
            neighbours.remove([x, y, move])

    # Abbruchbedingung: only "game over" tiles in vecinity
    if len(neighbours) == 0:
        return "", -1

    queue = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
    heapq.heapify(queue)
    pos = heapq.heappop(queue)
    steps += 1

    # pos: [heuristik, x,y,next_move]
    while (pos[1], pos[2]) != end:
        #get neighbours of pos
        neighbours = [[pos[1] + x, pos[2] + y, pos[3]] for x, y in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
        new_field = [[heuristik(x, y, end, steps), x, y, move] for x, y, move in neighbours]
        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]

        # remove fields with "game over" tile states
        # different avoid tiles as soon as its not a direct neighbor of position
        if (type(agent) is "Project.Agent.Agent.knight" and agent.health > 1) or steps > 10:
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        elif type(agent) is "Project.Agent.Agent.hunter":
            #zweites if-Statement notwendig, da andere Rollen am Index [0][1] kein Inhalt haben
            if agent.items[0][1] > 0 or steps > 10:
                avoid_tiles.remove(TileCondition.WUMPUS)
        for heuristik, x, y, move in new_field:
            if risky_tile(x,y, map_knowledge, avoid_tiles):
                new_field.remove([heuristik, x, y, move])
        # add non "game over" fields
        for tile in new_field:
            heapq.heappush(queue, tile)

        # Abbruchbedingung: kein Weg gefunden
        if len(queue) == 0:
            return "", -1

        pos = heapq.heappop(queue)
        steps += 1


    next_move = pos[3]
    states = map_knowledge.get_tile(pos[1],pos[2])
    if len(states) == 0: # unknown tile
        max_utility = field_utility[-1]
    else:
        max_utility = field_utility[states[0]]
        for index in range(1,len(states)):
            if field_utility[states[index]] > max_utility:
                max_utility = field_utility[states[index]]
    utility = max_utility/ pos[0]  #Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
    return next_move, utility



def utility_movement(map_knowledge: KnowledgeBase, agent):
    field_utility = goals_to_field_value(agent.goals)
    best_utility = {"right": -1, "left": -1, "up": -1, "down": -1}
    # best_utility nur negative Werte --> nicht bewegen / in die Wand laufen
    max_utility = 0
    next_move = "stay"
    #distance to fields which utility will be calculated
    # TODO: Sinnvolle Zahl? Change: braucht man nicht (siehe unten)
    MAX_DISTANCE = max(MAP_HEIGHT, MAP_WIDTH) // 3
    avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT, TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
    if AgentGoal.WUMPUS in agent.goals:
        avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
        avoid_tiles.remove(TileCondition.WUMPUS)
    # TODO: cartograf bekommt Menge von unbekannten Tiles, die angrenzt an Bekannten sind
    pos_row,pos_col = agent.position
    # TODO: mit Methode die Menge an relevanten Tiles bekommen (in calc-tiles speichern);
    # keine relevanten Tiles bekannt --> suche im unmittelbaren Bereich, damit man Gefahren aus dem Weg geht
    # calculate everything (timeconsuming) --> drop very far away tiles because their utility most likely will not be the best_utility for that move
    calc_tiles = [(row,col) for row in range(MAP_HEIGHT) for col in range(MAP_WIDTH) if abs(row-pos_row) + abs(col-pos_col) <= MAX_DISTANCE]
    for row,col in calc_tiles:
        tile = map_knowledge.get_tile(row,col)
        # Agenten wollen nur ein Stench-Feld mehrfach betrachten, weil ein Verschwinden von Stench anders nicht wahrgenommen werden kann
        if tile.visited() and not tile.tile_has_condition(TileCondition.STENCH):
            continue
        tile_conditions = tile.get_conditions()
        # cartograph wants to see entire map --> wants to go to unknown tiles
        # all agents except cartograph want to focus on known tiles
        if AgentGoal.MAP_PROGRESS not in agent.goals and len(tile_conditions) == 0:
            continue
        if risky_tile(row,col,map_knowledge,avoid_tiles): # skip undesired tiles
            continue
        move, utility = a_search(map_knowledge, (row,col), field_utility, agent)
        if utility > best_utility[move]:
            best_utility[move] = utility
        if utility > max_utility:
            next_move = move
            max_utility = utility
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

# probability for states:
# wumpus: neben Gold und in Räumen (0.5)
# gold: spawn in dead-ends (0.3)
# pits: in Räumen (0.3)
# dead ends: ?
# Raum: 1/6
# -->echte Wahrscheinlichkeiten
# pits: 3/10*1/6 = 3/60 = 1/20
# gold: deadend_prob * 3/10 = ...
# deadend_prob numerisch ermitteln
# wumpus = (gold + (1-3/10)*1/6 ) * 1/2


def utility_information(fields, agent, map_knowledge: KnowledgeBase):
    # expected utiltiy of area based on probabilities for map generation
    deadend_prob = agent.getNumDeadEnds() / (MAP_HEIGHT*MAP_WIDTH)
    gold_prob = deadend_prob * 0.3
    wumpus_prob = (gold_prob + 0.7*1/6)*0.5
    amount = len(fields)
    if AgentGoal.WUMPUS in agent.goals and AgentGoal.GOLD in agent.goals:
        return (gold_prob + wumpus_prob) * amount
    if AgentGoal.WUMPUS in agent.goals:
        return wumpus_prob * amount
    if AgentGoal.GOLD in agent.goals:
        return gold_prob * amount
    # only cartographer left
    return amount

def utility_gold(agent, gold_amount):
    field_utility = goals_to_field_value(agent.goals)
    return gold_amount * field_utility[TileCondition.SHINY]

def utility_help_wumpus(agent):
    # can not fight wumpus --> decline
    if "wumpus" not in agent.goals:
        return 0
    # knight wants gold for action--> less utility than for hunter (so he'll get the utility via gold from other agent)
    if "wumpus" in agent.goals and "gold" in agent.goals:
        return goals_to_field_value(agent.goals)[TileCondition.WUMPUS]/2
    # only hunter left
    return goals_to_field_value(agent.goals)[TileCondition.WUMPUS]

# nur für Anfang der Kommunikation
# --> cfp : help und position


# bool'sche Ausgabe, ob eine Kommunikation angenommen werden soll
def accept_communication(map_knowledge : KnowledgeBase, agent, request_type: RequestTypeObj):
    if request_type == RequestTypeObj.HELP:
        # hunter and knight accept Communication and later decide dependent on their arrows/health
        return "wumpus" not in agent.goals
    else: # position (information exchange)
        # agent only engages in information exchange if he doesnt have a goal-tile in his knowledge
        def get_goal_states(goals): # cartograph nicht Teil, da er vor Aufruf der Methode schon terminiert
            states = []
            if AgentGoal.WUMPUS in goals:
                states.append(TileCondition.WUMPUS)
            if AgentGoal.GOLD in goals:
                states.append(TileCondition.SHINY)
            return states

        # cartograph always wants to gain new information
        if AgentGoal.MAP_PROGRESS in agent.goals:
            return True

        goal_states = get_goal_states(agent.goals)
        for row in range(MAP_HEIGHT):
            for col in range(MAP_WIDTH):
                for condition in goal_states:
                    if map_knowledge.tile_has_condition(row,col,condition):
                        return False
        return True

def utility_():
    pass
from typing import Union

from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
from enum import Enum
from Project.communication.protocol import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject
from Project.Simulator import REPLENISH_TIME, grid
import heapq  # für a*-search

MAX_UTILITY = 200
NUM_DEADENDS = grid.numDeadEnds  #  notwendig zur Berechnung des Erwartungswert einer Menge von Feldern

class AgentRole(Enum):
    HUNTER: int = 0
    CARTOGRAPHER: int = 1
    KNIGHT: int = 2
    BWL_STUDENT: int = 3


class AgentAction(Enum):
    MOVE_UP: int = 0
    MOVE_LEFT: int = 1
    MOVE_RIGHT: int = 2
    MOVE_DOWN: int = 3
    PICK_UP: int = 4
    SHOOT_UP: int = 5
    SHOOT_LEFT: int = 6
    SHOOT_RIGHT: int = 7
    SHOOT_DOWN: int = 8
    SHOUT: int = 9


class AgentItem(Enum):
    GOLD: int = 0
    ARROW: int = 1


class AgentGoal(Enum):
    GOLD: int = 0
    WUMPUS: int = 1
    MAP_PROGRESS: int = 2


class Agent:
    def __init__(self, name: int, role: AgentRole, goals: set[AgentGoal], gold_visibility_range: int,
                 spawn_position: tuple[int, int], map_width: int, map_height: int):
        # set a single time
        self.__name: int = name
        self.__role: AgentRole = role
        self.__goals: set[AgentGoal] = goals
        self.__utility = Utility(goals, map_height, map_width)
        self.__gold_visibility_range: int = gold_visibility_range

        # knowledge
        self.__knowledge: KnowledgeBase = KnowledgeBase(spawn_position, map_width, map_height)

        # status (information given by simulator each step)
        self.__position: tuple[int, int] = (0, 0)
        self.__health: int = 0
        self.__items: list[int] = []
        self.__available_item_space: int = 0
        self.__time = 0

    def start_communication(self, agents: list[tuple[int, AgentRole]]) \
            -> tuple[list[int], tuple[OfferedObjects, RequestedObjects]]:
        """choose agents to communicate with and offer to make"""
        # TODO decision making for choosing agents to communicate with
        agents_to_communicate_with: list[int] = []
        roles_to_communicate_with: list[AgentRole] = []
        for agent in agents:
            agents_to_communicate_with.append(agent[0])
            roles_to_communicate_with.append(agent[1])
        if agents_to_communicate_with:
            return agents_to_communicate_with, self.create_offer(roles_to_communicate_with)
        return agents_to_communicate_with, None



    def create_offer(self, receivers: list[AgentRole]) -> tuple[OfferedObjects, RequestedObjects]:
        # TODO: decision making for making offers

        # offer
        offered_gold: int = 0
        offered_tiles: list[tuple[int, int, list[TileCondition]]] = []
        offered_wumpus_positions: list[tuple[int, int]] = []

        # request
        requested_gold: int = 0
        requested_tiles: list[tuple[int, int]] = []
        requested_wumpus_positions: int = 0

        return OfferedObjects(offered_gold, offered_tiles, offered_wumpus_positions), RequestedObjects(requested_gold,
                                                                                                       requested_tiles,
                                                                                                       requested_wumpus_positions)

    def create_counter_offer(self, receiver: AgentRole, offer: Offer) -> tuple[OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO decision making for creating counter offers
        pass

    def answer_to_offer(self, sender: tuple[int, AgentRole], offer: Offer) -> tuple[
        ResponseType, OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO: decision making for offers

        return ResponseType.ACCEPT, None, None

    def check_offer_satisfaction(self, best_offer: OfferedObjects, request: RequestedObjects) -> tuple[int, bool]:
        #expected_offer_utility = utility(request)
        #if utility(best_offer) >= expected_offer_utility:
            #return (expected_offer_utility, True)
        #else:
            #return (expected_offer_utility, False)


    def receive_tile_information(self, position: tuple[int, int], tile_conditions: [TileCondition], health: int,
                                 items: list[int], available_item_space: int, time: int):
        self.__position: tuple[int, int] = position
        self.__knowledge.update_position(self.__position)
        self.__knowledge.update_tile(position[0], position[1], tile_conditions)
        self.__health = health
        self.__items = items
        self.__available_item_space = available_item_space
        self.__time = time

    def get_next_action(self) -> AgentAction:
        # TODO: implementation
        pass

    def apply_changes(self, sender, receiver, request, offer):
        #TODO: match case was für ein request/offer das hier ist und apply auf self.sender und self.receiver
        pass

    def start_negotiation(self:, receiver: Agent, best_offer):
        # TODO: negotiation algorithmn: Concession Protocol Page 24
        s_expected_utility = self.Utility.offer_utility(best_offer)
        r_expected_utility =  receiver.Utility.offer_utility(best_offer)
        negotiation_round = 0
        limit = 5
        conflict_deal = False
        current_offer = best_offer
        while negotiation_round < limit:
            negotiation_round+=1
            s_offer = self.create_counter_offer(self.__role, current_offer)
            r_offer = receiver.create_counter_offer(receiver.__role, current_offer)

            #if one Agent agrees to the others offer
            if  s_expected_utility >=  self.Utility.offer_utility(r_offer):
                current_offer = r_offer
                break

            elif  r_expected_utility >=  self.Utility.offer_utility(s_offer):
                current_offer = s_offer
                break
                   
    #else: die mit besser utility für beide ist current offer
            current_offer = s_offer #?
        if negotiation_round == limit:
            print(f"The negotiation has failed, conflict deal reached")
        else:
            print(f"The negotiation is completed, with {current_offer} as the accepted offer")
            self.apply_changes(self, receiver, current_offer)


    def receive_shout_action_information(self, x: int, y: int):
        self.__knowledge.add_shout(x, y, self.__time)

    def receive_bump_information(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, [TileCondition.WALL])

    def get_position(self):
        return self.__position

    def get_knowledge(self):
        return self.__knowledge

    def get_utility(self):
        return self.__utility

    def get_role(self):
        return self.__role

    def get_itemspace(self):
        return self.__available_item_space
    def get_items(self):
        return self.__items
    def can_fight(self):
        return self.__health > 1

class Hunter(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int,
                 map_height: int):
        super().__init__(name, AgentRole.HUNTER, {AgentGoal.WUMPUS}, gold_visibility,
                         spawn_position, map_width, map_height)


class Cartographer(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int,
                 map_height: int):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, gold_visibility, spawn_position,
                         map_width, map_height)


class Knight(Agent):
    def __init__(self, name, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, gold_visibility, spawn_position,
                         map_width, map_height)


class BWLStudent(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int,
                 map_height: int):
        super().__init__(name, AgentRole.BWL_STUDENT, {AgentGoal.GOLD}, gold_visibility, spawn_position, map_width,
                         map_height)

class Utility:
    def __init__(self, goals, map_height, map_width):
        self.__field_utility: dict = self.goals_to_field_value(goals)
        self.__map_height = map_height
        self.__map_width = map_width

    def goals_to_field_value(self, goals: set[AgentGoal]):
        field_utility: dict = {}
        if AgentGoal.WUMPUS in goals and AgentGoal.GOLD in goals:
            ranks = 6
            field_utility[TileCondition.WUMPUS] = MAX_UTILITY
            field_utility[TileCondition.SHINY] = MAX_UTILITY
            field_utility[TileCondition.PREDICTED_WUMPUS] = MAX_UTILITY - (ranks - 5) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.STENCH] = MAX_UTILITY - (ranks - 4) * float(MAX_UTILITY / ranks)
            field_utility[-1] = MAX_UTILITY - (ranks - 3) * float(MAX_UTILITY / ranks)  #unknown
            field_utility[TileCondition.SAFE] = MAX_UTILITY - (ranks - 2) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.BREEZE] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_PIT] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WALL] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PIT] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            return field_utility

        if AgentGoal.WUMPUS in goals:
            ranks = 7
            field_utility[TileCondition.WUMPUS] = MAX_UTILITY
            field_utility[TileCondition.PREDICTED_WUMPUS] = MAX_UTILITY - (ranks - 6) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.STENCH] = MAX_UTILITY - (ranks - 5) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.SHINY] = MAX_UTILITY - (ranks - 4) * float(MAX_UTILITY / ranks)
            field_utility[-1] = MAX_UTILITY - (ranks - 3) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.SAFE] = MAX_UTILITY - (ranks - 2) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.BREEZE] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_PIT] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WALL] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PIT] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            return field_utility

        if AgentGoal.GOLD in goals:
            ranks = 4
            field_utility[TileCondition.SHINY] = MAX_UTILITY
            field_utility[-1] = MAX_UTILITY - (ranks - 3) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.SAFE] = MAX_UTILITY - (ranks - 2) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.STENCH] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.BREEZE] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_WUMPUS] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_PIT] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WALL] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WUMPUS] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PIT] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            return field_utility

        if AgentGoal.MAP_PROGRESS in goals:
            ranks = 4
            field_utility[-1] = MAX_UTILITY
            field_utility[TileCondition.SAFE] = MAX_UTILITY - (ranks - 3) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.SHINY] = MAX_UTILITY - (ranks - 2) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.STENCH] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.BREEZE] = MAX_UTILITY - (ranks - 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_PIT] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PREDICTED_WUMPUS] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WALL] = MAX_UTILITY - ranks* float(MAX_UTILITY / ranks)
            field_utility[TileCondition.WUMPUS] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            field_utility[TileCondition.PIT] = MAX_UTILITY - (ranks + 1) * float(MAX_UTILITY / ranks)
            return field_utility

    # Funktion: Ist ein Tile für den Agenten sicher
    # Ausgabe: bool
    def risky_tile(self, pos_row, pos_col, map_knowledge: KnowledgeBase, risky_tile_states):
        for state in risky_tile_states:
            if state in map_knowledge.get_conditions_of_tile(pos_row, pos_col):
                return True
        return False
    
    # Funktion: shortes path berechnen
    # Ausgabe: (move: AgentAction, utility: float)
    def a_search(self, end, agent: Agent):

        def heuristik(pos_row, pos_col, end, steps, map_knowledge: KnowledgeBase):
            end_row, end_col = end
            # unbekannte Tiles haben schlechteren heuristischen Wert, weil unklar ist, ob der Weg nutzbar ist
            if len(map_knowledge.get_conditions_of_tile(pos_row,pos_col)) == 0:
                return (abs(pos_row - end_row) + abs(pos_col - end_col) + steps) * 2
            return abs(pos_row - end_row) + abs(pos_col - end_col) + steps

        map_knowledge = agent.get_knowledge()
        pos_row, pos_col = agent.get_position()

        # Abbruchbedingung: already on end-field
        if (pos_row, pos_col) == end:
            return None , -1

        steps = 1
        neighbours = [[pos_row + row, pos_col + col, move] for row, col, move in
                      [[0, 1, AgentAction.MOVE_RIGHT], [1, 0, AgentAction.MOVE_UP], [0, -1, AgentAction.MOVE_LEFT], [-1, 0, AgentAction.MOVE_DOWN]]]

        # avoid certain tilestates if it's a direct neighbour
        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                       TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
        if agent.get_role() == AgentRole.KNIGHT and agent.can_fight():
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        for row, col, move in neighbours:
            if self.risky_tile(row, col, map_knowledge, avoid_tiles):
                neighbours.remove([row, col, move])

        # Abbruchbedingung: only "game over" tiles as neighbours (kann theoretisch nich eintreten)
        if len(neighbours) == 0:
            return "", -1

        queue = [[heuristik(row, col, end, steps, map_knowledge), row, col, move] for row, col, move in neighbours]
        heapq.heapify(queue)
        pos = heapq.heappop(queue)
        steps += 1

        # pos: [heuristik, x,y,next_move]
        while (pos[1], pos[2]) != end:
            #get neighbours of pos
            neighbours = [[pos[1] + row, pos[2] + col, pos[3]] for row, col in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
            new_field = [[heuristik(row, col, end, steps, map_knowledge), row, col, move] for row, col, move in neighbours]
            avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                           TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]

            # remove fields with "game over" tile states
            # different avoid tiles as soon as it's not a direct neighbour of position
            if agent.get_role() == AgentRole.KNIGHT and (agent.can_fight() or steps > REPLENISH_TIME): # TODO: steps > REPLENISH_TIME - turn % REPLENISH_TIME
                avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
                avoid_tiles.remove(TileCondition.WUMPUS)
            elif agent.get_role() == AgentRole.HUNTER and (agent.get_items()[AgentItem.ARROW.value()] > 0 or steps > REPLENISH_TIME): # TODO: wie oben
                avoid_tiles.remove(TileCondition.WUMPUS)
            for heuristik, row, col, move in new_field:
                if self.risky_tile(row, col, map_knowledge, avoid_tiles):
                    new_field.remove([heuristik, row, col, move])

            # add non "game over" fields
            for tile in new_field:
                heapq.heappush(queue, tile)

            # Abbruchbedingung: kein Weg gefunden
            if len(queue) == 0:
                return "", -1

            pos = heapq.heappop(queue)
            steps += 1

        next_move = pos[3]
        states = map_knowledge.get_conditions_of_tile(pos[1], pos[2])
        if len(states) == 0:  # unknown tile
            max_utility = self.__field_utility[-1]
        else:
            max_utility = None
            for state in states:
                if max_utility is None or self.__field_utility[state] > max_utility:
                    max_utility = self.__field_utility[state]

        # reduziere Utility von Felder, auf denen Agenten kürzlich waren (reduziert Loopgefahr)
        if (pos[1], pos[2]) in map_knowledge.get_path()[-5:]:
            max_utility = 1
        utility = max_utility / pos[0]  # Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
        return next_move, utility
    
    # Funktion: Ermittle Rangordnung der nächstmöglichen moves 
    # Ausgabe: (next_move: Agent_Action, best_utility: dict)
    def utility_movement(self, agent: Agent):
        map_knowledge = agent.get_knowledge()
        best_utility = {AgentAction.MOVE_RIGHT: -1, AgentAction.MOVE_LEFT: -1, AgentAction.MOVE_UP: -1, AgentAction.MOVE_DOWN: -1}
        max_utility = None
        next_move = None
        calc_tiles = []

        match agent.get_role():
            case AgentRole.CARTOGRAPHER:
                calc_tiles = map_knowledge.get_closest_unknown_tiles_to_any_known_tiles()
                calc_tiles += map_knowledge.get_closest_unvisited_tiles()
                calc_tiles = list(set(calc_tiles))
            case AgentRole.KNIGHT:
                for condition in [TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS , TileCondition.STENCH, TileCondition.SHINY]:
                    calc_tiles += map_knowledge.get_tiles_by_condition(condition)
            case AgentRole.HUNTER:
                for condition in [TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS , TileCondition.STENCH]:
                    calc_tiles += map_knowledge.get_tiles_by_condition(condition)
            case AgentRole.BWL_STUDENT:
                calc_tiles = map_knowledge.get_tiles_by_condition(TileCondition.SHINY)
        # Agenten haben keine goal (affiliated) tiles in der Knowledgebase
        if len(calc_tiles) == 0:
            calc_tiles = map_knowledge.get_closest_unknown_tiles_to_any_known_tiles()
            calc_tiles += map_knowledge.get_closest_unvisited_tiles()
            calc_tiles = set(calc_tiles)

        for row, col in calc_tiles:
            # nur Stench-Tiles sollen mehrfach besucht werden können (Herausfinden ob Wumpus getötet wurde)
            if map_knowledge.visited(row, col) and not map_knowledge.tile_has_condition(row, col, TileCondition.STENCH):
                continue
            move, utility = self.a_search((row, col), agent)
            if utility > best_utility[move]:
                best_utility[move] = utility

        # get best move
        for move in best_utility.keys():
            if max_utility is None or best_utility[move] > max_utility:
                next_move = move
                max_utility = best_utility[move]
        return next_move, best_utility

    # Funktion: Ermittle utility einer Menge von Feldern
    #  utility of unknown fields --> Erwartungswert
    # Wahrscheinlichkeiten basieren auf Wahrscheinlichkeiten in der map-generation
    # Ausgabe: utility: double
    # TODO: Differenzierung zwischen known und unknown Feldmengen 
    def utility_information(self, fields, agent: Agent):
        deadend_prob = NUM_DEADENDS / (self.__map_height * self.__map_width)
        gold_prob = deadend_prob * 0.3
        wumpus_prob = (gold_prob + 0.7 * 1 / 6) * 0.5
        amount = len(fields)
        match agent.get_role():
            case AgentRole.KNIGHT:
                return (gold_prob + wumpus_prob) * amount
            case AgentRole.HUNTER:
                return wumpus_prob * amount
            case AgentRole.CARTOGRAPHER:
                return amount
            case AgentRole.BWL_STUDENT:
                return gold_prob * amount

    # Ausgabe: utility: double
    def utility_gold(self, gold_amount):
        return gold_amount * self.__field_utility[TileCondition.SHINY]
    
    # Funktion: Ermittle utility einem anderen Agenten mit KILL_WUMPUS zu helfen
    def utility_help_wumpus(self, agent: Agent):
        match agent.get_role():
            # knight also wants gold for helping out --> less utility than for hunter who'll always help
            case AgentRole.KNIGHT:
                return self.__field_utility[TileCondition.WUMPUS] / 4
            case AgentRole.HUNTER:
                return self.__field_utility[TileCondition.WUMPUS]
            case _:  # rest cant kill wumpus
                return 0

    # TODO: Methode: Berechnung eines eigenen Offers
    # Voraussetzung: Vor Methodenaufruf wurde festgestellt, dass der Agent eine Kommunikation starten möchte
    # Überlegung:
    # - help_request Liste nicht leer --> Cfp/Request kill wumpus
    # - rest: request/cfp tile_information
    # Ausgabe: RequestObject
    # performativ hängt von Agenten in der Umgebung ab --> nicht für die Funktion relevant
    # TODO: Frage: Hunter/Knight: Service anbieten einbauen? Wenn ja, wie sieht die Message dazu aus
    def get_offer_type(self, agent: Agent):
        if len(agent.get_contracts()) > 0:
            # TODO: help_request Liste nicht leer --> Cfp/Request kill wumpus (Auftrag-Attribut notwendig)
            return RequestObject.KILL_WUMPUS
        return RequestObject.TILE_INFORMATION


    # Überlegungen: Welche Felder sind von Interesse
    # Wumpuskiller wollen Infos zu Wumpus --> wollen PREDICTED_WUMPUS als WUMPUS aufdecken --> Frage andere Agenten nach den Felder + angrenzende Felder
    # keine PREDICTED_WUMPUS bekannt --> erkundeten Bereich ausweiten --> Wissen über Felder notwendig, die an visited tiles angrenzen
    # -->
    # KNIGHT / HUNTER:
    #   1. PREDICTED_WUMPUS und neighboring unknown tiles (anderer Agent, kann mehr dazu wissen --> wumpus besser erkennbar)
    #   2. unknown tiles grenzend an visited tiles
    # BWL_STUDENT / CARTOGRAPH:
    #   1. unknown tiles grenzend an visited tiles

    # Funktion: Ermittle, über welche tiles ein Agent Information haben möchte
    # Ausgabe: tiles: list[tuple(int,int)]
    def offer_wanted_tiles(self, agent: Agent):
        knowledge = agent.get_knowledge()
        if agent.get_role() in [AgentRole.KNIGHT, AgentRole.HUNTER]:
            pred_wumpus_tiles = knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS)
            # keine PREDICTED_WUMPUS tiles in der Knowledgebase --> closest unvisited tiles
            if len(pred_wumpus_tiles) == 0:
                return knowledge.get_closest_unvisited_tiles()
            # add pred_wumpus and unknown neighbours of pred_wumpus to wanted tiles
            wanted_tiles = pred_wumpus_tiles
            for tile in pred_wumpus_tiles:
                pos_row, pos_col = tile
                neighbours = [(row+pos_row,col+pos_col) for row,col in [(-1,0),(1,0),(0,-1),(0,1)] if 0 <= row+pos_row < self.__map_height and 0 <= col+pos_col < self.__map_width]
                for new_tile in neighbours:
                    row, col = new_tile
                    # add unknown tile
                    if len(knowledge.get_conditions_of_tile(row,col)) == 0:
                        wanted_tiles.add(new_tile)
            return set(wanted_tiles)

        # BWL-Student und Cartograph übrig --> closest unvisited tiles
        return knowledge.get_closest_unvisited_tiles()

    # TODO: Frage: notwendig?
    # Szenario:
    # Agent1 will x Felder | Agent2 will y Felder
    # Agent1 hat nur über z Felder Information (z<y),Agent2 hat knowledge über w Felder Infos ( w = x oder w > z
    # Agent1 muss im counteroffer seine Menge an Felder verändern sodass es nur noch z Felder sind
    def counteroffer_wanted_tiles(self, agent: Agent, other_utility):
        pass

    # get: Agent der Funktion ausführt bekommt (give trivial)
    # Überlegung:
    #   Abbruchbedingungen: Es wird etwas angefragt, was der Agent nicht hat
    #   Ermittle Utility von get und give
    #   return ob differenz positiv ist

    # Funktion: Werte aus, ob ein Angebot eines Agentens annehmbar für den Agenten ist
    # Ausgabe: bool

    def evaluate_offer(self, agent: Agent, get_type: RequestObject, get_content: Union[int, list[tuple[int,int]]], give_type: RequestObject, give_content: Union[int, list[tuple[int,int]]]):
        # calculate give_utility
        give_utility = 0
        match give_type:
            case RequestObject.KILL_WUMPUS:
                if agent.get_role() in [AgentRole.BWL_STUDENT, AgentRole.CARTOGRAPHER]:
                    return False
                give_utility = self.utility_help_wumpus(agent)* give_content
            case RequestObject.GOLD:
                if agent.get_items()[AgentItem.GOLD.value] < give_content:
                    return False
                give_utility = self.utility_gold(give_content)
            case RequestObject.TILE_INFORMATION:
                # get amount of known fields in give content
                known_tiles = give_content
                for row,col in give_content:
                    if len(agent.get_knowledge().get_conditions_of_tile(row,col)) == 0:
                        known_tiles.remove((row,col))
                # TODO: Frage: soll tile_utility von goals des anderen Agenten abhängen?
                give_utility = self.utility_information(known_tiles, agent)
        # calculate get_utility
        get_utility = 0
        match get_type:
            case RequestObject.KILL_WUMPUS:
                # hunter und knight brauchen keine Hilfe zum killen von Wumpus
                if agent.get_role() in [AgentRole.KNIGHT, AgentRole.HUNTER]:
                    return False
                get_utility = MAX_UTILITY/2* give_content
            case RequestObject.GOLD:
                get_utility = self.utility_gold(agent, min(get_content, agent.get_itemspace()))
            case RequestObject.TILE_INFORMATION:
                # TODO: Annahme, dass get_content nur Felder beinhaltet, die der andere Agent kennt/knowledge hat
                give_utility = self.utility_information(get_content, agent)

        return give_utility-get_utility <= 0

    # get: ausführender Agent bekommt (give trivial)
    # Funktion wird bei Beginn einer Kommunikation ausgeführt --> performativ vernachlässigbar

    # Funktion: Ermittle, ob der Agent die eingehende Kommunikation annhemen möchte
    # Ausgabe: bool
    def accept_communication(self, agent, get_object: RequestObject, give_object: RequestObject):
        # TODO: wenn agent ein Auftrag hat, soll er sich nur damit befassen --> keine Kommunikation annehmen
        # TODO: Prüfe, ob in der Kommunikation eine Liste vom Request_objects behandelt wird
        #   falls ja, überarbeite match-case

        match give_object:
            case RequestObject.KILL_WUMPUS:
                return agent.get_role() in [AgentRole.KNIGHT, AgentRole.HUNTER]
            case RequestObject.GOLD:
                return agent.get_items()[AgentItem.GOLD] > 0
        match get_object:
            case RequestObject.KILL_WUMPUS:
                return agent.get_role() not in [AgentRole.KNIGHT, AgentRole.HUNTER]
            case RequestObject.GOLD:
                return agent.get_itemspace() > 0
            case RequestObject.TILE_INFORMATION:
                # Agent geht nur auf Informationsaustausch ein, wenn er keine Information über seine eigenen Ziele besitzt
                goal_states = []
                match agent.get_role():
                    case AgentRole.CARTOGRAPHER:
                        return True
                    case AgentRole.KNIGHT:
                        goal_states = [TileCondition.WUMPUS, TileCondition.SHINY]
                    case AgentRole.HUNTER:
                        goal_states = [TileCondition.WUMPUS]
                    case AgentRole.BWL_STUDENT:
                        goal_states = [TileCondition.SHINY]
                for condition in goal_states:
                    if len(agent.get_knowledge().get_tiles_by_condition(condition)) > 0:
                        return False
                return True

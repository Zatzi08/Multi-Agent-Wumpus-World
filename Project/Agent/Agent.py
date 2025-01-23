
from typing import Union

from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
from enum import Enum
from Project.communication.protocol import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject
import heapq  # für a*-search

MAX_UTILITY = 200
ACCEPTABLE_TILE_FACTOR = 0.2
REPLENISH_TIME = 32
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
    def __init__(self, name: int, role: AgentRole, goals: set[AgentGoal], spawn_position: tuple[int, int],
                 map_width: int, map_height: int, replenish_time: int, map_info: dict):
        # set a single time
        self.__name: int = name
        self.__role: AgentRole = role
        self.__goals: set[AgentGoal] = goals
        self.__utility = Utility(goals, map_height, map_width)
        self.__replenish_time: int = replenish_time

        # knowledge
        self.__knowledge: KnowledgeBase = KnowledgeBase(spawn_position, map_width, map_height)

        # status (information given by simulator each step)
        self.__position: tuple[int, int] = (0, 0)
        self.__health: int = 0
        self.__items: list[int] = []
        self.__available_item_space: int = 0
        self.__time = 0
        self.__map_info = map_info

    #
    # next agent move
    #

    def get_next_action(self) -> AgentAction:
        pos_row, pos_col = self.__position
        height, width = self.__utility.get_dimensions()
        # shoot wumpus
        if self.__items[AgentItem.ARROW.value()] > 0:
            for row,col,action in [(pos_row+row,pos_col+col, action) for row,col,action in [(1,0, AgentAction.SHOOT_DOWN),(-1,0, AgentAction.SHOOT_UP),(0,1, AgentAction.SHOOT_RIGHT),(0,-1, AgentAction.SHOOT_LEFT)] if 0 <= pos_row+row < height and 0 <= pos_col+col < width]:
                if self.__knowledge.tile_has_condition(row,col,TileCondition.WUMPUS):
                    return action

        # on gold-tile
        if self.__knowledge.tile_has_condition(pos_row,pos_col, TileCondition.SHINY) and self.__available_item_space > 0:
            # hunter soll kein Gold aufsammeln,wenn es sein itemslot für arrow blockiert
            if not (self.__role == AgentRole.HUNTER and self.__available_item_space == 1 and self.__items[AgentItem.ARROW.value()] == 0):
                return AgentAction.PICK_UP

        # normal Bewegung ermitteln
        return self.get_movement()

    #
    # agent knowledge
    #

    def receive_tile_information(self, position: tuple[int, int], tile_conditions: list[TileCondition], health: int,
                                 items: list[int], available_item_space: int, time: int):
        self.__position: tuple[int, int] = position
        self.__knowledge.update_position(self.__position)
        self.__knowledge.update_tile(position[0], position[1], tile_conditions)
        self.__health = health
        self.__items = items
        self.__available_item_space = available_item_space
        self.__time = time

    def receive_shout_action_information(self, x: int, y: int):
        self.__knowledge.add_shout(x, y, self.__time)

    def receive_bump_information(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, [TileCondition.WALL])

    def receive_gold_position(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, [TileCondition.SHINY])

    def receive_tiles_with_condition(self, tiles: list[tuple[int, int]], condition: TileCondition) -> None:
        for tile in tiles:
            self.__knowledge.update_tile(tile[0], tile[1], [condition])

    def get_map(self) -> list[list[set[TileCondition]]]:
        return self.__knowledge.return_map()

    #
    # communication
    #

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


    # Annahme: abhängig von dem RequestObject sind Argumente wie desired_tiles, acceptable_tiles und wumpus_amount 0 oder empty
    # Idee: erstes offer ist maxed out, damit counter-offer auf eine Reduktion des offers beschränkt ist
    def create_offer(self, desired_tiles: set[tuple[int, int]], acceptable_tiles: set[tuple[int, int]], knowledge_tiles: set[tuple[int, int]], other_gold_amount: int, other_wumpus_amount: int) -> tuple[OfferedObjects, RequestedObjects]:

        # offer
        offered_gold: int = 0
        offered_tiles: list[tuple[int, int, list[TileCondition]]] = []
        offered_wumpus_positions: list[tuple[int, int]] = []

        # request
        requested_gold: int = other_gold_amount
        requested_tiles: list[tuple[int, int]] = []
        requested_wumpus_positions: int = other_wumpus_amount

        # get request_tiles
        my_desired_tiles = self.desired_tiles()
        req_desired_tiles = my_desired_tiles.intersection(knowledge_tiles)
        req_acceptable_tiles = self.acceptable_tiles(my_desired_tiles).intersection(knowledge_tiles)
        requested_tiles = list(req_acceptable_tiles.union(req_desired_tiles))
        request_utility = self.utility_help_wumpus() * requested_wumpus_positions + self.utility_gold() * requested_gold + self.utility_information(req_desired_tiles)+ self.utility_information(req_acceptable_tiles) + ACCEPTABLE_TILE_FACTOR

        # get offer
        offer_utility = 0

        #tile-info
        #agents want tile_info
        if len(desired_tiles) > 0:
            off_desired_tiles = [(row,col,list(self.__knowledge.get_conditions_of_tile(row,col))) for row,col in desired_tiles if len(self.__knowledge.get_conditions_of_tile(row,col)) > 0]
            if self.utility_information(off_desired_tiles) > request_utility:
                reduced_amount = int(len(off_desired_tiles) * request_utility / self.utility_information(off_desired_tiles))
                offered_tiles = off_desired_tiles[:reduced_amount]
                return OfferedObjects(offered_gold, offered_tiles, offered_wumpus_positions), RequestedObjects(requested_gold, requested_tiles, requested_wumpus_positions)
            offered_tiles = off_desired_tiles
            offer_utility += self.utility_information(off_desired_tiles)
        if len(acceptable_tiles) > 0:
            off_acceptable_tiles = [(row,col,list(self.__knowledge.get_conditions_of_tile(row,col))) for row,col in acceptable_tiles if len(self.__knowledge.get_conditions_of_tile(row,col)) > 0]
            if self.utility_information(off_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR + offer_utility > request_utility:
                reduced_amount = int(len(off_acceptable_tiles) * request_utility / (self.utility_information(off_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR))
                offered_tiles = offered_tiles.union(off_acceptable_tiles[:reduced_amount])
                return OfferedObjects(offered_gold, offered_tiles, offered_wumpus_positions), RequestedObjects(requested_gold, requested_tiles, requested_wumpus_positions)
            offered_tiles = offered_tiles.union(off_acceptable_tiles)
            offer_utility += self.utility_information(off_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR

        #wumpus-positions
        # TODO: henrys Meinung:  kein offer-wumpus-positions, weil bei Empfänger der nicht wumpus jagt, das offer immer abgelehnt wird
        #    UND die wumpus-positions eh in einem Kommunkationsversuch vom BWL_STUDENT und CARTOGRAPHER behandelt werden
        #   Frage: ist das für euch in Ordnung?

        # gold
        # Agents, die gold als ziel haben nutzen es nicht als Handelsgut (es als Handelsgut zu nutzen, wird meistens zu keinem Erflogreichen Austausch führen)
        if self.__role is [AgentRole.HUNTER, AgentRole.CARTOGRAPHER]:
            max_gold_amount = int((request_utility - offer_utility) / self.utility_gold())
            offered_gold = min(max_gold_amount, self.__items[AgentItem.GOLD.value()])
        return OfferedObjects(offered_gold, offered_tiles, offered_wumpus_positions), RequestedObjects(requested_gold, requested_tiles, requested_wumpus_positions)

    def create_counter_offer(self, offer: Offer, desired_tiles: set[tuple[int, int]], acceptable_tiles: set[tuple[int, int]], knowledge_tiles: set[tuple[int, int]], other_gold_amount: int, other_wumpus_amount: int) -> tuple[OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO decision making for creating counter offers

        # Ist ein Counteroffer noch zu machen --> ermittle Differenz der utilities
        offer_utility = offer.off_gold * self.utility_gold()
        request_utility = offer.req_gold * self.utility_gold()

        # offer-wumpus-pos ignoriert, weil get_offer immer off_wumpus_pos = 0 hat (siehe obige erklärung)
        offer_desired_subset = offer.off_tiles.intersection(desired_tiles)
        offer_acceptable_subset = offer.off_tiles.intersection(acceptable_tiles)
        offer_utility += self.utility_information(offer_desired_subset) + self.utility_information(offer_acceptable_subset) * ACCEPTABLE_TILE_FACTOR
        my_desired_tiles = self.desired_tiles()
        request_desired_subset = offer.req_tiles.intersection(my_desired_tiles)
        request_acceptable_subset = offer.req_tiles.intersection(self.acceptable_tiles(my_desired_tiles))
        request_utility += self.utility_information(request_desired_subset) + self.utility_information(request_acceptable_subset) * ACCEPTABLE_TILE_FACTOR
        if request_utility <= offer_utility + 1:
            return None
        diff_utility = request_utility - offer_utility
        current_diff_utility = diff_utility
        request_gold = offer.req_gold
        request_wumpus_positions = offer.req_wumpus_positions
        request_tiles = offer.req_tiles

        if offer.req_gold > 0:
            reduce_gold_amount = int(diff_utility / self.utility_gold())
            request_gold -= reduce_gold_amount
            current_diff_utility -= reduce_gold_amount * self.utility_gold()
        if current_diff_utility <= diff_utility / 2:
            return OfferedObjects(offer.off_gold,offer.off_tiles,offer.off_wumpus_positions), RequestedObjects(request_gold,request_tiles, request_wumpus_positions)

        if len(offer.req_tiles) > 0:
            my_acceptable_tiles = offer.req_tiles.union(knowledge_tiles)
            if current_diff_utility < self.utility_information(my_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR:
                reduced_amount = int(len(my_acceptable_tiles) * current_diff_utility / (self.utility_information(my_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR))
                request_tiles = request_tiles.difference(my_acceptable_tiles[reduced_amount:])
                return OfferedObjects(offer.off_gold,offer.off_tiles,offer.off_wumpus_positions), RequestedObjects(request_gold,request_tiles, request_wumpus_positions)
            request_tiles = request_tiles.difference(my_acceptable_tiles)



        pass

    def answer_to_offer(self, sender: tuple[int, AgentRole], offer: Offer) -> tuple[
        ResponseType, OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO: decision making for offers

        return ResponseType.ACCEPT, None, None


    def apply_changes(self, sender, receiver, request, offer):
        #TODO: match case was für ein request/offer das hier ist und apply auf self.sender und self.receiver
        pass

# TODO: participants zu int, AgentRole umschreiben, CounterOffer Pffer pder OfferedObjects als Eingabe?
    def start_negotiation(self, receivers: list[int, AgentRole], receiver_offers: dict[int, tuple[ResponseType, OfferedObjects, RequestedObjects]]):
        # the sender has constant request, the receivers are changing their offer to fit the sender
        negotiation_round = 0
        limit = 3
        request = next(iter(receiver_offers.values()[2]))
        good_offers: dict[tuple[int, AgentRole]:Offer] = {}
        best_utility = -1
        best_offer: dict[int, tuple[OfferedObjects, RequestedObjects]] = {}

        print("A negotiation has started!")
        while negotiation_round < limit:
            negotiation_round += 1
            for participant, answer in receiver_offers:
                offer_utility = Agent.evaluate_offer(self, answer[1], answer[2])
                if offer_utility > -1:
                    good_offers.update({participant: participant.create_counter_offer(Offer(request, receiver_offers[participant][2], participant[1]))})

            if len(good_offers) > 0:
                print("Good offers are found, looking for the best")
                for participant, p_answer in good_offers.items():
                    offer_utility = Agent.evaluate_offer(self, p_answer[1], p_answer[2])
                    if offer_utility > best_utility:
                        best_utility = offer_utility
                        best_offer = {participant: (p_answer[1], p_answer[2])}

                break

        if best_offer:
            print(f"The negotiation has reached an agreement with offer: {best_offer.values()} from {best_offer.keys()}")

        else:
            print(f"The negotiation has failed")


    #
    # utility
    #

    # Funktion: shortes path berechnen
    # Ausgabe: (move: AgentAction, utility: float)
    def a_search(self, end):

        def heuristik(pos_row, pos_col, end, steps, map_knowledge: KnowledgeBase):
            end_row, end_col = end
            # unbekannte Tiles haben schlechteren heuristischen Wert, weil unklar ist, ob der Weg nutzbar ist
            if len(map_knowledge.get_conditions_of_tile(pos_row,pos_col)) == 0:
                return (abs(pos_row - end_row) + abs(pos_col - end_col) + steps) * 2
            return abs(pos_row - end_row) + abs(pos_col - end_col) + steps

        pos_row, pos_col = self.__position

        # Abbruchbedingung: already on end-field
        if (pos_row, pos_col) == end:
            return None , -1

        steps = 1
        neighbours = [[pos_row + row, pos_col + col, move] for row, col, move in
                      [[0, 1, AgentAction.MOVE_RIGHT], [1, 0, AgentAction.MOVE_UP], [0, -1, AgentAction.MOVE_LEFT], [-1, 0, AgentAction.MOVE_DOWN]]]

        # avoid certain tilestates if it's a direct neighbour
        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                       TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
        if self.__role== AgentRole.KNIGHT and self.__health > 1:
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        for row, col, move in neighbours:
            if risky_tile(row, col, self.__knowledge, avoid_tiles):
                neighbours.remove([row, col, move])

        # Abbruchbedingung: only "game over" tiles as neighbours (kann theoretisch nich eintreten)
        if len(neighbours) == 0:
            return "", -1

        queue = [[heuristik(row, col, end, steps, self.__knowledge), row, col, move] for row, col, move in neighbours]
        heapq.heapify(queue)
        pos = heapq.heappop(queue)
        steps += 1

        # pos: [heuristik, x,y,next_move]
        while (pos[1], pos[2]) != end:
            #get neighbours of pos
            neighbours = [[pos[1] + row, pos[2] + col, pos[3]] for row, col in [[0, 1], [1, 0], [0, -1], [-1, 0]]]
            new_field = [[heuristik(row, col, end, steps, self.__knowledge), row, col, move] for row, col, move in neighbours]
            avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                           TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]

            # remove fields with "game over" tile states
            # different avoid tiles as soon as it's not a direct neighbour of position
            if self.__role == AgentRole.KNIGHT and (self.__health > 1 or steps > REPLENISH_TIME):
                avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
                avoid_tiles.remove(TileCondition.WUMPUS)
            elif self.__role == AgentRole.HUNTER and (self.__items[AgentItem.ARROW.value()] > 0 or steps > REPLENISH_TIME):
                avoid_tiles.remove(TileCondition.WUMPUS)
            for heuristik, row, col, move in new_field:
                if risky_tile(row, col, self.__knowledge, avoid_tiles):
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
        states = self.__knowledge.get_conditions_of_tile(pos[1], pos[2])
        if len(states) == 0:  # unknown tile
            max_utility = self.__utility.get_utility_of_condition(-1)
        else:
            max_utility = None
            for state in states:
                if max_utility is None or self.__utility.get_utility_of_condition(state) > max_utility:
                    max_utility = self.__utility.get_utility_of_condition(state)

        # reduziere Utility von Felder, auf denen Agenten kürzlich waren (reduziert Loopgefahr)
        if (pos[1], pos[2]) in self.__knowledge.get_path()[-5:]:
            max_utility = 1
        utility = max_utility / pos[0]  # Utility des Feldes dividiert durch Anzahl an Schritte bis zum Feld
        return next_move, utility

    # Funktion: Ermittle Rangordnung der nächstmöglichen moves
    # Ausgabe: (next_move: Agent_Action, best_utility: dict)
    def get_movement(self):
        best_utility = {AgentAction.MOVE_RIGHT: -1, AgentAction.MOVE_LEFT: -1, AgentAction.MOVE_UP: -1, AgentAction.MOVE_DOWN: -1}
        max_utility = None
        next_move = None
        calc_tiles = []
        if len(self.__knowledge.get_kill_wumpus_tasks()) > 0:
            calc_tiles = self.__knowledge.get_kill_wumpus_tasks()
        else:
            match self.__role:
                case AgentRole.CARTOGRAPHER:
                    calc_tiles = self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles()
                    calc_tiles += self.__knowledge.get_closest_unvisited_tiles()
                    calc_tiles = list(set(calc_tiles))
                case AgentRole.KNIGHT:
                    for condition in [TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS , TileCondition.STENCH, TileCondition.SHINY]:
                        calc_tiles += self.__knowledge.get_tiles_by_condition(condition)
                case AgentRole.HUNTER:
                    for condition in [TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS , TileCondition.STENCH]:
                        calc_tiles += self.__knowledge.get_tiles_by_condition(condition)
                case AgentRole.BWL_STUDENT:
                    calc_tiles = self.__knowledge.get_tiles_by_condition(TileCondition.SHINY)
            # Agenten haben keine goal (affiliated) tiles in der Knowledgebase
            if len(calc_tiles) == 0:
                calc_tiles = self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles()
                calc_tiles += self.__knowledge.get_closest_unvisited_tiles()
                calc_tiles = set(calc_tiles)

        for row, col in calc_tiles:
            # nur Stench-Tiles sollen mehrfach besucht werden können (Herausfinden ob Wumpus getötet wurde)
            if self.__knowledge.visited(row, col) and not self.__knowledge.tile_has_condition(row, col, TileCondition.STENCH):
                continue
            move, utility = self.a_search((row, col))
            if utility > best_utility[move]:
                best_utility[move] = utility

        # get best move
        for move in best_utility.keys():
            if max_utility is None or best_utility[move] > max_utility:
                next_move = move
                max_utility = best_utility[move]
        if max_utility < 0:
            next_move = AgentAction.SHOUT
        return next_move

    # Funktion: Ermittle utility einer Menge von Feldern
    #  utility of unknown fields --> Erwartungswert
    # Wahrscheinlichkeiten basieren auf Wahrscheinlichkeiten in der map-generation
    # Ausgabe: utility: double
    def utility_information(self, fields):
        wumpus_prob = len(self.__map_info[TileCondition.WUMPUS.value()])/len(self.__map_info["locations"])
        gold_prob = len(self.__map_info[TileCondition.SHINY.value()])/len(self.__map_info["locations"])
        match self.__role:
            case AgentRole.KNIGHT:
                return (wumpus_prob+gold_prob) * len(fields)
            case AgentRole.HUNTER:
                return wumpus_prob * len(fields)
            case AgentRole.CARTOGRAPHER:
                return len(fields)
            case AgentRole.BWL_STUDENT:
                return gold_prob * len(fields)

    # Ausgabe: utility: double
    def utility_gold(self):
        return 2 * self.__utility.get_utility_of_condition(TileCondition.SHINY)

    # Funktion: Ermittle utility einem anderen Agenten mit KILL_WUMPUS zu helfen
    def utility_help_wumpus(self):
        match self.__role:
            # knight also wants gold for helping out --> less utility than for hunter who'll always help
            case AgentRole.KNIGHT:
                return self.__utility.get_utility_of_condition(TileCondition.WUMPUS) / 8
            case AgentRole.HUNTER:
                return self.__utility.get_utility_of_condition(TileCondition.WUMPUS) / 2
            case _:  # rest cant kill wumpus
                return 0

    # TODO: Methode: Berechnung eines eigenen Offers
    # Voraussetzung: Vor Methodenaufruf wurde festgestellt, dass der Agent eine Kommunikation starten möchte
    # Überlegung:
    # - help_request Liste nicht leer --> Cfp/Request kill wumpus
    # - rest: request/cfp tile_information
    # Ausgabe: RequestObject
    # performativ hängt von Agenten in der Umgebung ab --> nicht für die Funktion relevant
    def get_offer_type(self):
        if len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)) > 0:
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
    def desired_tiles(self):
        if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
            pred_wumpus_tiles = self.__knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS)
            # keine PREDICTED_WUMPUS tiles in der Knowledgebase --> closest unvisited tiles
            if len(pred_wumpus_tiles) == 0:
                return self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles().intersection(self.__knowledge.get_closest_unvisited_tiles())
            # add pred_wumpus and unknown neighbours of pred_wumpus to wanted tiles
            wanted_tiles = pred_wumpus_tiles
            height, width = self.__utility.get_dimensions()
            for tile in pred_wumpus_tiles:
                pos_row, pos_col = tile
                neighbours = [(row+pos_row,col+pos_col) for row,col in [(-1,0),(1,0),(0,-1),(0,1)] if 0 <= row+pos_row < height and 0 <= col+pos_col < width]
                for new_tile in neighbours:
                    row, col = new_tile
                    # add unknown tile
                    if len(self.__knowledge.get_conditions_of_tile(row,col)) == 0:
                        wanted_tiles.add(new_tile)
            return set(wanted_tiles)

        # BWL-Student und Cartograph übrig --> closest unvisited tiles
        return self.__knowledge.get_closest_unvisited_tiles()

    # unknown tiles, die nicht an known/visited-tiles angrenzen
    def acceptable_tiles(self, desired_tiles: set[tuple[int, int]]):
        height, width = self.__utility.get_dimensions()
        all_tiles = [(row,col) for row in range(height) for col in range(width)]
        # Agent will neue Infos zu bekannten tiles
        if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER] and len(self.__knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS)) > 0:
            non_acceptable_tiles = []
        else:
            non_acceptable_tiles = self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles().intersection(self.__knowledge.get_closest_unvisited_tiles())
        acceptable_tiles = []
        for tile in all_tiles:
            row, col = tile
            if tile in non_acceptable_tiles:
                continue
            if len(self.__knowledge.get_conditions_of_tile(row,col)) == 0:
                acceptable_tiles.append(tile)
        # desired tiles und acceptable_tiles dürfen keine Schnittmenge haben, da Funktionen unter der Annahme arbeiten
        return set(acceptable_tiles).difference(desired_tiles)


    # TODO: Geh durch, welche noch notwendigen Funktionen welche utility-methoden nutzen müssen
    # Funktion: Ermittle auf Basis eines offers ein neues counteroffer (für tiles und jegliches andere)
    # Ausgabe: counter_offer : OfferedObject
    # TODO: get_counteroffer mit Dynamic Programming (mit Gruppe andere Ansätze diskutieren)
    def get_counteroffer(self, offer: Offer, desired_tiles: set[tuple[int, int]], acceptable_tiles: set[tuple[int, int]], knowledge_tiles: set[tuple[int, int]], other_agent_gold_amount: int, other_agent_wumpus_amount: int):
        new_offer = Offer(OfferedObjects(0, [], []), RequestedObjects(0,[], 0), self.__role)
        # Abbruchbedingung: kein besseres Angebot möglich, ohne selber negative utility zu erhalten
        give_utility = self.utility_information(offer.off_tiles) + self.utility_gold() * offer.off_gold + 20 * len(offer.off_wumpus_positions)
        get_utility = self.utility_information(offer.req_tiles) + self.utility_gold() * offer.req_gold + self.utility_help_wumpus() * offer.req_wumpus_positions
        # wenn sie zu nah beieinander sind, ist kein besseres offer möglich ohne selber eine negative utility zu haben
        # TODO: ist 5 ein guter Wert?
        if give_utility >= get_utility + 5:
            return None
        diff_utility = get_utility - give_utility
        # Ziel: added_utility = diff_utility / 2 (immer näher an Gleichheit rangehen)

        # Prüfe ob aktuelles Offer/Request das maximum sind
        # array: [gold, wumpus, tile]
        max_off = [True, True, True]
        max_req = [True, True, True]
        # Agent will Gold als tradegut nutzen
        if self.__role in [AgentRole.HUNTER, AgentRole.CARTOGRAPHER]:
            if offer.req_gold < self.__items[AgentItem.GOLD.value]:
                max_off[0] = False

        # Hunter und Knight wollen keine Wumpus_info preis geben (nicht das ihnen der kill geklaut wird)
        if self.__role in [AgentRole.BWL_STUDENT, AgentRole.CARTOGRAPHER]:
            if len(offer.off_wumpus_positions) < len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)):
                max_off[1] = False

        # off_tiles is empty --> keine Schnittmenge mit geforderten tiles oder anderer Agent will keine tileInfo
        # --> TileInfo nicht tradebar
        available_acceptable_tiles, available_desired_tiles = [],[]
        if len(offer.off_tiles) > 0:
            # kann der Agent noch mehr tiles anbieten?
            available_acceptable_tiles = set([(row,col) for row,col in acceptable_tiles if len(self.__knowledge.get_conditions_of_tile(row, col)) > 0])
            available_desired_tiles = set([(row,col) for row,col in desired_tiles if len(self.__knowledge.get_conditions_of_tile(row, col)) > 0])
            if len(offer.off_tiles) < len(available_desired_tiles.union(available_acceptable_tiles)):
                max_off[2] = False

        # nur diese Rollen, weil anderer Agent sonst eine höhere utility dem Gol zuordent und somit das angebot sehr wahrscheinlich abgelehnt wird
        if self.__role in [AgentRole.KNIGHT, AgentRole.BWL_STUDENT]:
            if offer.req_gold < self.__available_item_space:
                max_req[0] = False
        if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
            if offer.req_wumpus_positions < other_agent_wumpus_amount:
                max_req[1] = False
        # Agent möchte Tileinfo und anderer Agent hat nutzbare Infos
        my_desired_tiles, my_acceptable_tiles = [], []
        if len(offer.req_tiles) > 0:
            my_desired_tiles = self.desired_tiles().intersection(knowledge_tiles)
            my_acceptable_tiles = self.acceptable_tiles(self.desired_tiles()).intersection(knowledge_tiles)
            if len(offer.req_tiles) < len(my_desired_tiles.union(my_acceptable_tiles)):
                max_req[2] = False

        current_diff_utility = diff_utility
        # Erste Cases: nur einer der beiden kann reduziert werden
        # request muss reduziert werden
        if False not in max_off and False in max_req:
            if len(offer.req_tiles) > 0:
                req_acceptable_tiles = my_acceptable_tiles.intersection(offer.req_tiles)
                req_desired_tiles = my_desired_tiles.intersection(offer.req_tiles)
                utility_req_acceptable_tiles = self.utility_information(req_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR
                utility_req_desired_tiles = self.utility_information(req_desired_tiles)
                if current_diff_utility - utility_req_acceptable_tiles < 0:
                    reduced_acceptable_tiles = self.reduce_tiles(req_acceptable_tiles, utility_req_acceptable_tiles - current_diff_utility, True)
                    new_offer.req_tiles = reduced_acceptable_tiles.union(req_desired_tiles) # hat was mit TO DO zu tun
                    return new_offer
                if current_diff_utility - utility_req_acceptable_tiles < diff_utility/2:
                    new_offer.req_tiles = req_desired_tiles
                    return new_offer
                if current_diff_utility - utility_req_desired_tiles - utility_req_acceptable_tiles < 0:
                    reduced_desired_tiles = self.reduce_tiles(req_desired_tiles, utility_req_desired_tiles - current_diff_utility, False)
                    new_offer.req_tiles = reduced_desired_tiles # hat was mit TO DO zu tun
                    return new_offer
                if current_diff_utility - utility_req_desired_tiles - utility_req_acceptable_tiles < diff_utility/2:
                    new_offer.req_tiles = []
                    return new_offer
            if offer.req_wumpus_positions > 0:
                if offer.req_gold > 0 and 0 < current_diff_utility - self.utility_gold():
                    potential_req_gold = offer.req_gold - 1
                    current_diff_utility -= self.utility_gold()
            if








    # get: Agent der Funktion ausführt bekommt (give trivial)
    # Überlegung:
    #   Abbruchbedingungen: Es wird etwas angefragt, was der Agent nicht hat
    #   Ermittle Utility von get und give
    #   return ob differenz positiv ist

    # Funktion: Werte aus, ob ein Angebot eines Agentens annehmbar für den Agenten ist
    # Ausgabe: bool
    # offer: anderer bietet mir ... | request: anderer möchte ...
    def evaluate_offer(self, offer: OfferedObjects, request: RequestedObjects):
        # calculate give_utility
        give_utility = 0
        if request.gold > 0:
            if self.__items[AgentItem.GOLD.value] < request.gold:
                return -1
            give_utility += self.utility_gold() * request.gold
        if request.wumpus_positions > 0:
            if request.wumpus_positions > len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)):
                return -1
            if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
                give_utility += self.utility_help_wumpus() * request.wumpus_positions
            elif self.__role in [AgentRole.BWL_STUDENT, AgentRole.CARTOGRAPHER]:
                # utiltiy, dass denen ein Wumpus gekillt wird
                give_utility += MAX_UTILITY/2* request.wumpus_positions
        if len(request.tiles) > 0:
            # Durch negotiating-Konzept muss keine Überprüfung der tile-Menge geamcht werden
            give_utility += self.utility_information(request.tiles)

        # calculate get_utility
        get_utility = 0
        if offer.gold_amount > 0:
            if self.__available_item_space < offer.gold_amount:
                return -1
            get_utility += self.utility_gold() * offer.gold_amount
        if len(offer.wumpus_positions) > 0:
            if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
                get_utility += self.utility_help_wumpus() * offer.wumpus_positions
        if len(offer.tile_information)> 0:
            desired_tiles = self.desired_tiles()
            acceptable_tiles = self.acceptable_tiles(desired_tiles)
            get_utility += self.utility_information(desired_tiles) + self.utility_information(acceptable_tiles) * ACCEPTABLE_TILE_FACTOR
        return get_utility - give_utility

    # get: ausführender Agent bekommt (give trivial)
    # Funktion wird bei Beginn einer Kommunikation ausgeführt --> performativ vernachlässigbar

    # Funktion: Ermittle, ob der Agent die eingehende Kommunikation annhemen möchte
    # Ausgabe: bool
    def accept_communication(self, get_object: RequestObject, give_object: RequestObject):
        if len(self.__knowledge.get_kill_wumpus_tasks()) > 0:
            return False
        match give_object:
            case RequestObject.KILL_WUMPUS:
                return self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]
            case RequestObject.GOLD:
                return self.__items[AgentItem.GOLD.value] > 0
        match get_object:
            case RequestObject.KILL_WUMPUS:
                return self.__role not in [AgentRole.KNIGHT, AgentRole.HUNTER]
            case RequestObject.GOLD:
                return self.__available_item_space > 0
            case RequestObject.TILE_INFORMATION:
                # Agent geht nur auf Informationsaustausch ein, wenn er keine Information über seine eigenen Ziele besitzt
                if self.__role == AgentRole.CARTOGRAPHER:
                    return True
                goal_states = []
                match self.__role:
                    case AgentRole.KNIGHT:
                        goal_states = [TileCondition.WUMPUS, TileCondition.SHINY]
                    case AgentRole.HUNTER:
                        goal_states = [TileCondition.WUMPUS]
                    case AgentRole.BWL_STUDENT:
                        goal_states = [TileCondition.SHINY]
                for condition in goal_states:
                    if len(self.__knowledge.get_tiles_by_condition(condition)) > 0:
                        return False
                return True

class Hunter(Agent):
    def __init__(self, name: int, spawn_position: tuple[int, int], map_width: int, map_height: int,
                 replenish_time: int, map_info: dict):
        super().__init__(name, AgentRole.HUNTER, {AgentGoal.WUMPUS}, spawn_position, map_width, map_height,
                         replenish_time, map_info)


class Cartographer(Agent):
    def __init__(self, name: int, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int, map_info: dict):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, spawn_position, map_width, map_height,
                         replenish_time, map_info)


class Knight(Agent):
    def __init__(self, name, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int, map_info: dict):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, spawn_position, map_width,
                         map_height, replenish_time, map_info)


class BWLStudent(Agent):
    def __init__(self, name: int, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int, map_info: dict):
        super().__init__(name, AgentRole.BWL_STUDENT, {AgentGoal.GOLD}, spawn_position, map_width, map_height,
                         replenish_time, map_info)

def goals_to_field_value(goals: set[AgentGoal]):
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
def risky_tile(pos_row, pos_col, map_knowledge: KnowledgeBase, risky_tile_states):
    for state in risky_tile_states:
        if state in map_knowledge.get_conditions_of_tile(pos_row, pos_col):
            return True
    return False

class Utility:
    def __init__(self, goals, map_height, map_width):
        self.__field_utility: dict = goals_to_field_value(goals)
        self.__map_height = map_height
        self.__map_width = map_width

    def get_utility_of_condition(self, condition):
        return self.__field_utility[condition]

    def get_dimensions(self):
        return self.__map_height, self.__map_width

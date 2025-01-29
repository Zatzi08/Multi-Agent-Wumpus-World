from Project.Agent.KnowledgeBase import KnowledgeBase
from Project.Communication.Offer import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject
from Project.Environment.TileCondition import TileCondition
from Project.SimulatedAgent.AgentEnums import AgentGoal, AgentRole, AgentItem, AgentAction
import heapq  # für a*-search
from numpy import ndarray

MAX_UTILITY = 200
ACCEPTABLE_TILE_FACTOR = 0.2

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
        self.__last_goal_tiles = set()
        self.__path_to_goal_tile = []

    #
    # next agent move
    #
    def get_knowledgebase(self):
        return self.__knowledge


    def get_next_action(self) -> AgentAction:

        #print(f"{self.__name} : {self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles()} {self.__knowledge.get_closest_unvisited_tiles()}")

        pos_row, pos_col = self.__position
        height, width = self.__utility.get_dimensions()

        # on gold-tile
        if self.__knowledge.tile_has_condition(pos_row, pos_col,
                                               TileCondition.SHINY) and self.__available_item_space > 0:
            # hunter soll kein Gold aufsammeln,wenn es sein itemslot für arrow blockiert
            if not (self.__role == AgentRole.HUNTER and self.__available_item_space == 1 and self.__items[
                AgentItem.ARROW.value] == 0):
                #print(f"{self.__name} {AgentAction.PICK_UP}")
                return AgentAction.PICK_UP

        # shoot wumpus
        if self.__role == AgentRole.HUNTER and self.__items[AgentItem.ARROW.value] > 0:
            shoot_action = None
            for row, col, action in [(pos_row + row, pos_col + col, action) for row, col, action in
                                     [(1, 0, AgentAction.SHOOT_RIGHT), (-1, 0, AgentAction.SHOOT_LEFT),
                                      (0, 1, AgentAction.SHOOT_UP), (0, -1, AgentAction.SHOOT_DOWN)] if
                                     0 <= pos_row + row < height and 0 <= pos_col + col < width]:
                if self.__knowledge.tile_has_condition(row, col, TileCondition.WUMPUS):
                    #print(f"{self.__name} {action}")
                    return action
                if self.__knowledge.tile_has_condition(row, col, TileCondition.PREDICTED_WUMPUS):
                    shoot_action = action
            if shoot_action is not None:
                return shoot_action
        # normal Bewegung ermitteln
        return self.get_movement()

    #
    # agent knowledge
    #

    def receive_status_from_simulator(self, position: tuple[int, int], health: int, items: list[int],
                                      available_item_space: int, time: int):
        self.__position: tuple[int, int] = position
        self.__knowledge.update_position(self.__position)
        self.__health = health
        self.__items = items
        self.__available_item_space = available_item_space
        self.__time = time

    def receive_tile_from_simulator(self, x: int, y: int, tile_conditions: set[TileCondition]):
        self.__knowledge.update_tile(x, y, tile_conditions, True)

    def receive_shout_action_information(self, x: int, y: int):
        self.__knowledge.add_shout(x, y, self.__time)

    def receive_bump_information(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, {TileCondition.WALL})

    def receive_wumpus_scream(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, {TileCondition.SAFE})

    def receive_gold_position(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, {TileCondition.SHINY})

    def receive_tiles_with_condition(self, tiles: list[tuple[int, int]], condition: TileCondition) -> None:
        for tile in tiles:
            self.__knowledge.update_tile(tile[0], tile[1], {condition})

    def receive_tile_from_communication(self, x: int, y: int, conditions: set[TileCondition]) -> None:
        self.__knowledge.update_tile(x, y, conditions)

    def receive_tile_condition(self, x, y) -> set[TileCondition]:
        return self.__knowledge.get__Map().get_conditions_of_tile(x, y)

    def receive_found_wumpus(self) -> set[tuple[int, int]]:
        return self.__knowledge.get_found_wumpus()

    def return_map(self) -> list[list[set[TileCondition]]]:
        return self.__knowledge.return_map()

    def return_goals(self) -> set[AgentGoal]:
        return self.__goals

    def add_kill_wumpus_task(self, x: int, y: int) -> None:
        self.__knowledge.add_kill_wumpus_task(x, y)


    #
    # Communication
    #

    def start_communication(self, agents: list[tuple[int, AgentRole]], offer_type: RequestObject) \
            -> list[int]:
        """choose agents to communicate with and offer to make"""
        # decision making for choosing agents to communicate with
        agents_to_communicate_with: list[int] = []
        # if offer_type None -> initiator doesn't want to communicate
        if offer_type is not None:
            for agentID, _ in agents:
                agents_to_communicate_with.append(agentID)
        return agents_to_communicate_with

    # Annahme: abhängig von dem RequestObject sind Argumente wie desired_tiles, acceptable_tiles und wumpus_amount 0 oder empty
    # Idee: erstes offer ist maxed out, damit counter-offer auf eine Reduktion des offers beschränkt ist
    def create_offer(self, desired_tiles: set[tuple[int, int]], acceptable_tiles: set[tuple[int, int]],
                     knowledge_tiles: set[tuple[int, int]], other_gold_amount: int, other_wumpus_amount: int) -> tuple[
        OfferedObjects, RequestedObjects]:

        # offer
        offered_gold: int = 0
        offered_tiles: set[tuple[int, int, list[TileCondition]]] = set()
        offered_wumpus_positions: list[tuple[int, int]] = []

        # request
        requested_gold: int = other_gold_amount
        requested_tiles: set[tuple[int, int]] = set()
        requested_wumpus_positions: int = other_wumpus_amount

        # get request_tiles
        my_desired_tiles = self.desired_tiles()
        request_desired_tiles = my_desired_tiles.intersection(knowledge_tiles)
        request_acceptable_tiles = self.acceptable_tiles(my_desired_tiles).intersection(knowledge_tiles)
        requested_tiles = request_acceptable_tiles.union(request_desired_tiles)
        request_utility = self.utility_help_wumpus() * requested_wumpus_positions + self.utility_gold() * requested_gold + self.utility_information(
            request_desired_tiles) + self.utility_information(request_acceptable_tiles) + ACCEPTABLE_TILE_FACTOR

        # request no content
        if request_utility == 0:
            return None, None
        # get offer
        offer_utility = 0

        #tile_info
        #agents want tile_info
        if len(desired_tiles) > 0:
            offer_desired_tiles = [(row, col, list(self.__knowledge.get_conditions_of_tile(row, col))) for row, col in
                                   desired_tiles if len(self.__knowledge.get_conditions_of_tile(row, col)) > 0]
            if self.utility_information(offer_desired_tiles) > request_utility:
                reduced_amount = int(
                    len(offer_desired_tiles) * request_utility / self.utility_information(offer_desired_tiles))
                offered_tiles = set(offer_desired_tiles[:reduced_amount])
                return OfferedObjects(offered_gold, list(offered_tiles), offered_wumpus_positions), RequestedObjects(
                    requested_gold, list(requested_tiles), requested_wumpus_positions)
            offered_tiles = set(offer_desired_tiles)
            offer_utility += self.utility_information(offer_desired_tiles)
        if len(acceptable_tiles) > 0:
            offer_acceptable_tiles = [(row, col, list(self.__knowledge.get_conditions_of_tile(row, col))) for row, col
                                      in acceptable_tiles if len(self.__knowledge.get_conditions_of_tile(row, col)) > 0]
            if self.utility_information(
                    offer_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR + offer_utility > request_utility:
                reduced_amount = int(len(offer_acceptable_tiles) * request_utility / (
                        self.utility_information(offer_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR))
                offered_tiles = offered_tiles.union(set(offer_acceptable_tiles[:reduced_amount]))
                return OfferedObjects(offered_gold, list(offered_tiles), offered_wumpus_positions), RequestedObjects(
                    requested_gold, list(requested_tiles), requested_wumpus_positions)
            offered_tiles = offered_tiles.union(offer_acceptable_tiles)
            offer_utility += self.utility_information(offer_acceptable_tiles) * ACCEPTABLE_TILE_FACTOR

        # offer-wumpus ignorieren, weil das durch ein KILL_WUMPUS request eh behandelt wird
        # gold
        # Agents, die gold als ziel haben nutzen es nicht als Handelsgut (es als Handelsgut zu nutzen, wird meistens zu keinem Erflogreichen Austausch führen)
        if self.__role is [AgentRole.HUNTER, AgentRole.CARTOGRAPHER]:
            max_gold_amount = int((request_utility - offer_utility) / self.utility_gold())
            offered_gold = min(max_gold_amount, self.__items[AgentItem.GOLD.value()])

        # offer ohne content
        if offer_utility == 0:
            return None, None
        return OfferedObjects(offered_gold, list(offered_tiles), offered_wumpus_positions), RequestedObjects(
            requested_gold, list(requested_tiles), requested_wumpus_positions)

    # TODO Henry mit Paula reden über:
    #  1. OfferObjects:  off_tiles soll nicht tileCondition beinhalten,
    #  weil sonst in counter_offer die TileConditions für die tiles geholt werden müssen (unnötiger Aufwand)
    #  2. Was soll die Rückgabe von counter_offer sein, wenn kein neues Counteroffer erstellt wird? Aktuell: None
    def create_counter_offer(self, offer: Offer, desired_tiles: set[tuple[int, int]],
                             acceptable_tiles: set[tuple[int, int]]) -> tuple[
        OfferedObjects, RequestedObjects]:
        set_off_tiles = set(offer.off_tiles)
        set_req_tiles = set(offer.req_tiles)
        # Ist ein Counteroffer noch zu machen --> ermittle Differenz der utilities
        offer_utility = offer.off_gold * self.utility_gold()
        request_utility = offer.req_gold * self.utility_gold()

        # offer-wumpus-pos ignoriert, weil get_offer immer off_wumpus_pos = 0 hat (siehe obige erklärung)
        offer_desired_subset = set_off_tiles.intersection(desired_tiles)
        offer_acceptable_subset = set_off_tiles.intersection(acceptable_tiles)
        offer_utility += self.utility_information(offer_desired_subset) + self.utility_information(
            offer_acceptable_subset) * ACCEPTABLE_TILE_FACTOR
        my_desired_tiles = self.desired_tiles()
        request_desired_subset = set_req_tiles.intersection(my_desired_tiles)
        request_acceptable_subset = set_req_tiles.intersection(self.acceptable_tiles(my_desired_tiles))
        request_utility += self.utility_information(request_desired_subset) + self.utility_information(
            request_acceptable_subset) * ACCEPTABLE_TILE_FACTOR
        # Abbruchbedingung
        if request_utility <= offer_utility + 1:
            return None

        diff_utility = request_utility - offer_utility
        current_diff_utility = diff_utility
        request_gold = offer.req_gold
        request_wumpus_positions = offer.req_wumpus_positions
        request_tiles = set_req_tiles
        offer_tiles = [(row,col, list(self.__knowledge.get_conditions_of_tile(row,col))) for row,col in offer.off_tiles]
        if offer.req_gold > 0:
            reduce_gold_amount = int(diff_utility / self.utility_gold())
            request_gold -= reduce_gold_amount
            current_diff_utility -= reduce_gold_amount * self.utility_gold()

        # check if utility is low enough
        if current_diff_utility <= diff_utility / 2:
            return OfferedObjects(offer.off_gold, offer_tiles, list(offer.off_wumpus_positions)), RequestedObjects(
                request_gold, list(request_tiles), request_wumpus_positions)

        if len(offer.req_tiles) > 0:
            # reduce/remove acceptable tiles
            if current_diff_utility < self.utility_information(request_acceptable_subset) * ACCEPTABLE_TILE_FACTOR:
                reduced_amount = int(len(request_acceptable_subset) * current_diff_utility / (
                        self.utility_information(request_acceptable_subset) * ACCEPTABLE_TILE_FACTOR))
                request_tiles = request_tiles.difference(set(list(request_acceptable_subset)[reduced_amount:]))
                return OfferedObjects(offer.off_gold, offer_tiles,
                                      list(offer.off_wumpus_positions)), RequestedObjects(request_gold, list(request_tiles),
                                                                                          request_wumpus_positions)
            request_tiles = request_tiles.difference(request_acceptable_subset)
            current_diff_utility -= self.utility_information(request_acceptable_subset) * ACCEPTABLE_TILE_FACTOR

            # check if utilty is low enough
            if current_diff_utility <= diff_utility / 2:
                return OfferedObjects(offer.off_gold, offer_tiles,
                                      list(offer.off_wumpus_positions)), RequestedObjects(request_gold,
                                                                                          list(request_tiles),
                                                                                          request_wumpus_positions)

            # reduce/remove desired tiles
            if current_diff_utility < self.utility_information(request_desired_subset):
                reduced_amount = int(len(request_desired_subset) * current_diff_utility / self.utility_information(
                    request_desired_subset))
                request_tiles = request_tiles.difference(set(list(request_desired_subset)[reduced_amount:]))
                return OfferedObjects(offer.off_gold, offer_tiles,
                                      list(offer.off_wumpus_positions)), RequestedObjects(request_gold,
                                                                                          list(request_tiles),
                                                                                          request_wumpus_positions)
            request_tiles = request_tiles.difference(request_desired_subset)
            return OfferedObjects(offer.off_gold, offer_tiles, list(offer.off_wumpus_positions)), RequestedObjects(
                request_gold, list(request_tiles), request_wumpus_positions)

        # req_wumpus nicht behandelt, weil anderer größere Utility davon hat als man selbst --> Reduktion von req_wumpus hilft nicht

        # keine Veränderung möglich, ohne negative utility
        return None
    
    

    # TODO: answer_to_offer verändern, s.d. desired,acceptable, knowledge etc. vom initiator kommt
    def answer_to_offer(self, initiator_request: RequestObject, desired_tiles, acceptable_tiles, knowledge_tiles, gold_amount, wumpus_amount) -> tuple[
        bool, OfferedObjects, RequestedObjects]:
        wumpus_tiles = self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)

        accept = self.accept_communication(initiator_request)
        offer, request = None, None
        if accept:
            offer, request = self.create_offer(desired_tiles, acceptable_tiles, knowledge_tiles,gold_amount, wumpus_amount)
            

        return accept, offer, request

    #
    # utility
    #

    # Funktion: shortes path berechnen
    # Ausgabe: (move: AgentAction, utility: float)
    def new_a_search(self, goal_tiles):
        def get_heuristik(pos_row, pos_col, steps, goal_tiles):
            best_heuristik, heuristik= None, None
            for row, col in goal_tiles:
                utility = None
                if len(self.__knowledge.get_conditions_of_tile(row, col)) == 0:
                    utility = self.__utility.get_utility_of_condition(-1)
                else:
                    for condition in self.__knowledge.get_conditions_of_tile(row, col):
                        if utility is None or utility < self.__utility.get_utility_of_condition(condition):
                            utility = self.__utility.get_utility_of_condition(condition)
                heuristik = steps + float((abs(pos_row - row) + abs(pos_col - col)) / utility)
                if best_heuristik is None or best_heuristik < utility:
                    best_heuristik = heuristik
            return heuristik

        name = self.__name
        pos_row, pos_col = self.__position
        visited_map = ndarray(shape=self.__utility.get_dimensions()).astype(bool)
        visited_map.fill(False)
        visited_map[pos_row][pos_col] = True
        height, width = self.__utility.get_dimensions()

        if self.__position in goal_tiles.copy():
            goal_tiles.remove(self.__position)

        steps = 1
        neighbours = [[pos_row + row, pos_col + col, move] for row, col, move in
                      [[0, 1, [AgentAction.MOVE_UP]], [1, 0, [AgentAction.MOVE_RIGHT]], [0, -1, [AgentAction.MOVE_DOWN]],
                       [-1, 0, [AgentAction.MOVE_LEFT]]]]

        # avoid certain tilestates if it's a direct neighbour
        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                       TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
        if self.__role == AgentRole.KNIGHT and self.__health > 1:
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        for row, col, move in neighbours.copy():
            if not (0 <= row < width and 0 <= col < height):
                neighbours.remove([row, col, move])
                continue
            if risky_tile(row, col, self.__knowledge, avoid_tiles):
                neighbours.remove([row, col, move])

        # Abbruchbedingung: only "game over" tiles as neighbours (kann theoretisch nich eintreten)
        if len(neighbours) == 0:
            return AgentAction.SHOUT
        if len(neighbours) == 1:
            return neighbours[0][2][0]
        queue = [[get_heuristik(row, col, steps, goal_tiles), row, col, path] for row, col, path in neighbours]
        heapq.heapify(queue)
        pos = heapq.heappop(queue)
        visited_map[pos[1]][pos[2]] = True
        steps += 1

        # pos: [heuristik, x,y,next_move]
        while (pos[1], pos[2]) not in goal_tiles:
            #get neighbours of pos
            neighbours = [[pos[1] + row, pos[2] + col, pos[3] + [move]] for row, col, move in
                          [[0, 1, AgentAction.MOVE_UP], [1, 0, AgentAction.MOVE_RIGHT], [0, -1, AgentAction.MOVE_DOWN],
                           [-1, 0, AgentAction.MOVE_LEFT]] if 0 <= pos[1] + row < width and 0 <= pos[2] + col < height]

            avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                           TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]

            # remove fields with "game over" tile states
            # different avoid tiles as soon as it's not a direct neighbour of position
            if self.__role == AgentRole.KNIGHT and (self.__health > 1 or steps > self.__replenish_time):
                avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
                avoid_tiles.remove(TileCondition.WUMPUS)
            elif self.__role == AgentRole.HUNTER and (
                    self.__items[AgentItem.ARROW.value] > 0 or steps > self.__replenish_time):
                avoid_tiles.remove(TileCondition.WUMPUS)
            for row, col, move in neighbours.copy():
                if risky_tile(row, col, self.__knowledge, avoid_tiles):
                    neighbours.remove([row, col, move])

            new_field = [[get_heuristik(row, col, steps, goal_tiles), row, col, path] for row, col, path in
                         neighbours]
            # add non "game over" fields
            for tile in new_field:
                if not visited_map[tile[1]][tile[2]]:
                    heapq.heappush(queue, tile)

            # Abbruchbedingung: kein Weg gefunden
            if len(queue) == 0:
                return AgentAction.SHOUT

            pos = heapq.heappop(queue)
            visited_map[pos[1]][pos[2]] = True
            steps += 1

        self.__path_to_goal_tile = pos[3][1:]
        return pos[3][0]


    # Funktion: Ermittle Rangordnung der nächstmöglichen moves
    # Ausgabe: (next_move: Agent_Action, best_utility: dict)
    def get_movement(self):
        calc_tiles = set()

        name = self.__name
        time = self.__time
        if len(self.__knowledge.get_kill_wumpus_tasks()) > 0:
            calc_tiles = self.__knowledge.get_kill_wumpus_tasks()
        else:
            calc_tiles = self.__knowledge.get_closest_unknown_tiles_to_any_known_tiles()
            calc_tiles = calc_tiles.union(self.__knowledge.get_closest_unvisited_tiles())
            calc_tiles = set(calc_tiles)
            match self.__role:
                case AgentRole.KNIGHT:
                    if self.__health > 1:
                        goal_states = [TileCondition.WUMPUS, TileCondition.PREDICTED_WUMPUS]
                        if self.__available_item_space > 0:
                            goal_states.append(TileCondition.SHINY)
                        for condition in goal_states:
                            calc_tiles = calc_tiles.union(self.__knowledge.get_tiles_by_condition(condition))
                    else:
                        for tiles in self.__knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS):
                            neighbours = [(row + tiles[0], col + tiles[1]) for row, col in
                                          [(0, 1), (1, 0), (-1, 0), (0, -1)] if
                                          len(self.__knowledge.get_conditions_of_tile(row + tiles[0], col + tiles[1])) == 0]
                            calc_tiles = calc_tiles.union(set(neighbours))
                case AgentRole.HUNTER:
                    if self.__items[AgentItem.ARROW.value] > 0:
                        calc_tiles = calc_tiles.union(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS))
                        for tiles in self.__knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS):
                            neighbours = [(row + tiles[0], col + tiles[1]) for row, col in
                                          [(0, 1), (1, 0), (-1, 0), (0, -1)] if
                                          len(self.__knowledge.get_conditions_of_tile(row + tiles[0], col + tiles[1])) == 0 and 0 <= row + tiles[0] < self.__utility.get_dimensions()[1] and 0 <= col + tiles[1] < self.__utility.get_dimensions()[0] ]
                            calc_tiles = calc_tiles.union(set(neighbours))
                case AgentRole.BWL_STUDENT:
                    if self.__available_item_space > 0:
                        calc_tiles = calc_tiles.union(self.__knowledge.get_tiles_by_condition(TileCondition.SHINY))
        avoid_tiles = [TileCondition.WALL, TileCondition.PREDICTED_PIT, TileCondition.PIT,
                       TileCondition.PREDICTED_WUMPUS, TileCondition.WUMPUS]
        if self.__role == AgentRole.KNIGHT and self.__health > 1:
            avoid_tiles.remove(TileCondition.PREDICTED_WUMPUS)
            avoid_tiles.remove(TileCondition.WUMPUS)
        elif self.__role == AgentRole.HUNTER and self.__items[AgentItem.ARROW.value] > 0:
            avoid_tiles.remove(TileCondition.WUMPUS)
        for tile in calc_tiles.copy():
            if risky_tile(tile[0], tile[1], self.__knowledge, avoid_tiles):
                calc_tiles.remove(tile)
        #print(f"{self.__name} {calc_tiles}")
        # keine Goal-tiles --> geh zum besten Nachbarn
        # Case: Agent alles durchforstet und ist stuck
        if len(calc_tiles) == 0:
            stench_tiles = self.__knowledge.get_tiles_by_condition(TileCondition.STENCH)
            if len(stench_tiles) > 0:
                path = self.__knowledge.get_path()
                for index in range(len(path)):
                    if self.__knowledge.tile_has_condition(path[len(path)-1-index][0],path[len(path)-1-index][1], TileCondition.STENCH):
                        stench_tiles.remove(path[len(path)-1-index])
                        break
                if len(self.__last_goal_tiles.symmetric_difference(stench_tiles)) == 0 and len(self.__path_to_goal_tile) > 0:
                    next_action = self.__path_to_goal_tile[0]
                    self.__path_to_goal_tile = self.__path_to_goal_tile[1:]
                    return next_action
                self.__last_goal_tiles = stench_tiles
                return self.new_a_search(self.__knowledge.get_tiles_by_condition(TileCondition.STENCH))
            return AgentAction.SHOUT
        else:
            if len(calc_tiles.symmetric_difference(self.__last_goal_tiles)) == 0 and len(self.__path_to_goal_tile) > 0:
                next_action = self.__path_to_goal_tile[0]
                self.__path_to_goal_tile = self.__path_to_goal_tile[1:]
                return next_action
            self.__last_goal_tiles = calc_tiles
            return self.new_a_search(calc_tiles)

    # Funktion: Ermittle utility einer Menge von Feldern
    #  utility of unknown fields --> Erwartungswert
    # Wahrscheinlichkeiten basieren auf Wahrscheinlichkeiten in der map-generation
    # Ausgabe: utility: double
    def utility_information(self, fields):
        wumpus_prob = len(self.__map_info[TileCondition.WUMPUS.value]) / len(self.__map_info["locations"])
        gold_prob = len(self.__map_info[TileCondition.SHINY.value]) / len(self.__map_info["locations"])
        match self.__role:
            case AgentRole.KNIGHT:
                return (wumpus_prob + gold_prob) * len(fields)
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
    # Überlegung:
    # - help_request Liste nicht leer --> Cfp/Request kill wumpus
    # - rest: request/cfp tile_information
    # Ausgabe: RequestObject
    # performativ hängt von Agenten in der Umgebung ab --> nicht für die Funktion relevant
    def get_offer_type(self):
        if self.__role in [AgentRole.BWL_STUDENT, AgentRole.CARTOGRAPHER] and len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)) > 0:
            return RequestObject.KILL_WUMPUS
        match self.__role:
            case AgentRole.BWL_STUDENT:
                if self.__available_item_space > 0:
                    return RequestObject.TILE_INFORMATION
            case AgentRole.CARTOGRAPHER:
                return RequestObject.TILE_INFORMATION
            case AgentRole.KNIGHT:
                if (len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)) == 0 or
                        (self.__available_item_space > 0 and
                         len(self.__knowledge.get_tiles_by_condition(TileCondition.SHINY)) == 0 )):
                    return RequestObject.TILE_INFORMATION
            case AgentRole.HUNTER:
                if len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)) == 0:
                    return RequestObject.TILE_INFORMATION
        return None
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
                return self.__knowledge.get_closest_unvisited_tiles()
            # add pred_wumpus and unknown neighbours of pred_wumpus to wanted tiles
            wanted_tiles = pred_wumpus_tiles
            height, width = self.__utility.get_dimensions()
            for tile in pred_wumpus_tiles:
                pos_row, pos_col = tile
                neighbours = [(row + pos_row, col + pos_col) for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)] if
                              0 <= row + pos_row < height and 0 <= col + pos_col < width]
                for new_tile in neighbours:
                    row, col = new_tile
                    # add unknown tile
                    if len(self.__knowledge.get_conditions_of_tile(row, col)) == 0:
                        wanted_tiles.add(new_tile)
            return set(wanted_tiles)

        # BWL-Student und Cartograph übrig --> closest unvisited tiles
        return self.__knowledge.get_closest_unvisited_tiles()

    # unknown tiles, die nicht an known/visited-tiles angrenzen
    def acceptable_tiles(self, desired_tiles: set[tuple[int, int]]):
        height, width = self.__utility.get_dimensions()
        all_tiles = [(row, col) for row in range(height) for col in range(width)]
        # Agent will neue Infos zu bekannten tiles
        if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER] and len(
                self.__knowledge.get_tiles_by_condition(TileCondition.PREDICTED_WUMPUS)) > 0:
            non_acceptable_tiles = []
        else:
            non_acceptable_tiles = self.__knowledge.get_closest_unvisited_tiles()
        acceptable_tiles = [tile for tile in all_tiles if tile not in non_acceptable_tiles and len(self.__knowledge.get_conditions_of_tile(tile[0], tile[1])) == 0]
        # desired tiles und acceptable_tiles dürfen keine Schnittmenge haben, da Funktionen unter der Annahme arbeiten
        return set(acceptable_tiles).difference(desired_tiles)

    def knowledge_tiles(self):
        knowledge_tiles = set()
        for condition in TileCondition:
            tiles = self.__knowledge.get_tiles_by_condition(condition)
            if len(tiles) > 0:
                knowledge_tiles = knowledge_tiles.union(tiles)
        return knowledge_tiles


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
        give_utility, get_utility = 0, 0
        if request.gold > 0:
            if self.__items[AgentItem.GOLD.value] < request.gold:
                return -1
            give_utility += self.utility_gold() * request.gold
        if request.wumpus_positions > 0:
            if request.wumpus_positions > len(self.__knowledge.get_tiles_by_condition(TileCondition.WUMPUS)):
                return -1
            if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
                return -1
            elif self.__role in [AgentRole.BWL_STUDENT, AgentRole.CARTOGRAPHER]:
                # utiltiy, dass denen ein Wumpus gekillt wird
                get_utility += MAX_UTILITY / 2 * request.wumpus_positions
        if len(request.tiles) > 0:
            # Durch negotiating-Konzept muss keine Überprüfung der tile-Menge geamcht werden
            give_utility += self.utility_information(request.tiles)

        # calculate get_utility

        if offer.gold_amount > 0:
            if self.__available_item_space < offer.gold_amount:
                return -1
            get_utility += self.utility_gold() * offer.gold_amount
        if len(offer.wumpus_positions) > 0:
            if self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]:
                get_utility += self.utility_help_wumpus() * offer.wumpus_positions
        if len(offer.tile_information) > 0:
            desired_tiles = self.desired_tiles()
            acceptable_tiles = self.acceptable_tiles(desired_tiles)
            get_utility += self.utility_information(desired_tiles) + self.utility_information(
                acceptable_tiles) * ACCEPTABLE_TILE_FACTOR
        return get_utility - give_utility

    # get: ausführender Agent bekommt (give trivial)
    # Funktion wird bei Beginn einer Kommunikation ausgeführt --> performativ vernachlässigbar

    # Funktion: Ermittle, ob der Agent die eingehende Kommunikation annhemen möchte
    # Ausgabe: bool
    def accept_communication(self, communication_topic: RequestObject):
        if len(self.__knowledge.get_kill_wumpus_tasks()) > 0:
            return False
        match communication_topic:
            case RequestObject.KILL_WUMPUS:
                return self.__role in [AgentRole.KNIGHT, AgentRole.HUNTER]
            case RequestObject.GOLD:
                return self.__items[AgentItem.GOLD.value] > 0
            case RequestObject.TILE_INFORMATION:
                # Agent geht nur auf Informationsaustausch ein, wenn er keine Information über seine eigenen Ziele besitzt
                if self.__role == AgentRole.CARTOGRAPHER:
                    return True
                goal_states = []
                match self.__role:
                    case AgentRole.KNIGHT:
                        goal_states = [TileCondition.WUMPUS, TileCondition.SHINY]
                        if self.__available_item_space == 0:
                            goal_states.remove(TileCondition.SHINY)
                    case AgentRole.HUNTER:
                        goal_states = [TileCondition.WUMPUS]
                    case AgentRole.BWL_STUDENT:
                        if self.__available_item_space == 0:
                            return False
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
    def __init__(self, name: int, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int,
                 map_info: dict):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, spawn_position, map_width, map_height,
                         replenish_time, map_info)


class Knight(Agent):
    def __init__(self, name, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int,
                 map_info: dict):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, spawn_position, map_width,
                         map_height, replenish_time, map_info)


class BWLStudent(Agent):
    def __init__(self, name: int, spawn_position: tuple[int, int], map_width: int, map_height: int, replenish_time: int,
                 map_info: dict):
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
        field_utility[TileCondition.WALL] = MAX_UTILITY - ranks * float(MAX_UTILITY / ranks)
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

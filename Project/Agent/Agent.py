from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
from enum import Enum
from Project.communication.protocol import Offer, OfferedObjects, RequestedObjects, ResponseType


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

class Agent: # TODO: fieldUtility Funktion
    def __init__(self, name: int, role: AgentRole, goals: set[AgentGoal], gold_visibility_range: int,
                 spawn_position: tuple[int, int], map_width: int, map_height: int):
        # set a single time
        self.__name: int = name
        self.__role: AgentRole = role
        self.__goals: set[AgentGoal] = goals
        self.__gold_visibility_range: int = gold_visibility_range

        # knowledge
        self.__knowledge: KnowledgeBase = KnowledgeBase(spawn_position, map_width, map_height)

        # status (information given by simulator each step)
        self.__position: tuple[int, int] = (0, 0)
        self.__health: int = 0
        self.__items: list[int] = []
        self.__available_item_space: int = 0
        self.__time = 0

    def start_communication(self, agents: list[tuple[int, AgentRole]]) -> (list[int], OfferedObjects):
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

        return OfferedObjects(offered_gold, offered_tiles, offered_wumpus_positions), RequestedObjects(requested_gold, requested_tiles, requested_wumpus_positions)

    def create_counter_offer(self, receiver: AgentRole, offer: Offer) -> tuple[OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO decision making for creating counter offers
        pass

    def answer_offer(self, sender: tuple[int, AgentRole], offer: Offer) -> tuple[ResponseType, OfferedObjects, RequestedObjects]:
        # TODO analyse offer
        # TODO: decision making for offers

        return ResponseType.ACCEPT, None, None

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

    def receive_shout_action_information(self, x: int, y: int):
        self.__knowledge.add_shout(x, y, self.__time)

    def receive_bump_information(self, x: int, y: int):
        self.__knowledge.update_tile(x, y, [TileCondition.WALL])

class Hunter(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.HUNTER, {AgentGoal.WUMPUS}, gold_visibility,
                         spawn_position, map_width, map_height)

class Cartographer(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, gold_visibility, spawn_position, map_width, map_height)

class Knight(Agent):
    def __init__(self, name, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, gold_visibility, spawn_position, map_width, map_height)

class BWLStudent(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.BWL_STUDENT, {AgentGoal.GOLD}, gold_visibility, spawn_position, map_width, map_height)

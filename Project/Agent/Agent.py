from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
from enum import Enum

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

class Agent: # TODO: fildUtility Funktion
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

    def communicate(self, agents: list[tuple[int, AgentRole]]) -> tuple[bool, list[int]]:
        # accept: choose agents to communicate with
        # TODO: - akzeptiere Kommunikation (2 Funktionen für Sender/Empfänger)
        #       - gibt Offer
        #       - akzeptiere/evaluiere Offer -> ggf. Counteroffer
        #       - entgegennahme von Tasks/Contracts
        agents_to_communicate_with: list[int] = []
        for agent in agents:
            agents_to_communicate_with.append(agent[0])
        return True, agents_to_communicate_with

        # deny
        # return False, []

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
        pass

        self.__knowledge.add_shout(x, y, self.__time)

class Hunter(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.HUNTER, {AgentGoal.WUMPUS}, gold_visibility,
                         spawn_position, map_width, map_height)

    def receive_shout_action_information(self, x: int, y: int):
class Cartographer(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, gold_visibility, spawn_position, map_width, map_height)


class Knight(Agent):
    def __init__(self, name, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, gold_visibility, spawn_position, map_width, map_height)


class BWLStudent(Agent):
    def __init__(self, name: int, gold_visibility: int, spawn_position: tuple[int, int], map_width: int, map_height: int):
        super().__init__(name, AgentRole.BWL_STUDENT, {AgentGoal.GOLD}, gold_visibility, spawn_position, map_width, map_height)

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

DEFAULT_HEALTH: int = 1
DEFAULT_ITEM_CAPACITY: int = 5
DEFAULT_GOLD_VISIBILITY_DISTANCE: int = 0
REPLENISH_TIME: int = 5

class Agent:
    def __init__(self, name: int, role: AgentRole, goals: set[AgentGoal], item_capacity: int,
                 gold_visibility_range: int, spawn_position: tuple[int, int], health: int, items: list[tuple[AgentItem, int]]):
        # set a single time
        self.name: int = name
        self.role: AgentRole = role
        self.goals: set[AgentGoal] = goals
        self.item_capacity: int = item_capacity
        self.gold_visibility_range: int = gold_visibility_range

        # knowledge
        self.knowledge: KnowledgeBase = KnowledgeBase(name, spawn_position)

        # status (information given by simulator each step)
        self.position: tuple[int, int] = spawn_position
        self.health: int = health
        self.items: dict[AgentItem, int] = {}
        for item in AgentItem:
            self.items[item] = 0
        for item in items:
            self.items[item[0]] = item[1]

    def communicate(self, agents: list[tuple[int, AgentRole]]) -> tuple[bool, list[int]]:
        # accept: choose agents to communicate with
        agents_to_communicate_with: list[int] = []
        for agent in agents:
            agents_to_communicate_with.append(agent[0])
        return True, agents_to_communicate_with

        # deny
        # return False, []

    def receive_tile_information(self, x: int, y: int, tile_conditions: [TileCondition]):
        self.knowledge.update_tile(x, y, tile_conditions)
        self.knowledge.update_position(self.position)

    def get_next_action(self) -> AgentAction:
        call to utility here

    def replenish(self):
        pass


class Hunter(Agent):
    START_ARROWS: int = 5
    REPLENISH_ARROWS: int = 5

    def __init__(self, name: int, spawn_position: tuple[int, int]):
        super().__init__(name, AgentRole.HUNTER, {AgentGoal.WUMPUS}, DEFAULT_ITEM_CAPACITY,
                         DEFAULT_GOLD_VISIBILITY_DISTANCE, spawn_position, DEFAULT_HEALTH,
                         [(AgentItem.ARROW, Hunter.START_ARROWS)])

    def replenish(self):
        if self.items[AgentItem.ARROW] < Hunter.REPLENISH_ARROWS:
            self.items[AgentItem.ARROW] += 1


class Cartographer(Agent):
    def __init__(self, name: int, spawn_position: tuple[int, int]):
        super().__init__(name, AgentRole.CARTOGRAPHER, {AgentGoal.MAP_PROGRESS}, DEFAULT_ITEM_CAPACITY,
                         DEFAULT_GOLD_VISIBILITY_DISTANCE, spawn_position, DEFAULT_HEALTH, [])
        map mit allen waenden


class Knight(Agent):
    START_HEALTH: int = 3
    ITEM_CAPACITY: int = 3
    REPLENISH_HEALTH: int = 3

    def __init__(self, name, spawn_position: tuple[int, int]):
        super().__init__(name, AgentRole.KNIGHT, {AgentGoal.WUMPUS, AgentGoal.GOLD}, Knight.ITEM_CAPACITY,
                         DEFAULT_GOLD_VISIBILITY_DISTANCE, spawn_position, Knight.START_HEALTH, [])

    def replenish(self):
        if self.health < Knight.REPLENISH_HEALTH:
            self.health += 1


class BWLStudent(Agent):
    ITEM_CAPACITY: int = 10
    GOLD_VISIBILITY_DISTANCE: int = 2

    def __init__(self, name: int, spawn_position: tuple[int, int]):
        super().__init__(name, AgentRole.BWL_STUDENT, {AgentGoal.GOLD}, BWLStudent.ITEM_CAPACITY,
                         BWLStudent.GOLD_VISIBILITY_DISTANCE, spawn_position,  DEFAULT_HEALTH, [])

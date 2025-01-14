from Project.Agent.Agent import AgentRole, AgentItem, Agent, Hunter, Cartographer, Knight, BWLStudent


class SimulatedAgent:
    def __init__(self, name: int, role: AgentRole, spawn_position: tuple[int, int]):
        self.name: int = name
        self.role: AgentRole = role
        self.position: tuple[int, int] = spawn_position

        self.agent: Agent
        self.gold_visibility_distance: int
        self.health: int
        self.items: list[int]
        self.available_item_space: int
        match role:
            case AgentRole.HUNTER:
                self.agent = Hunter(name, HunterValue.GOLD_VISIBILITY_DISTANCE, spawn_position)
                self.gold_visibility_distance = HunterValue.GOLD_VISIBILITY_DISTANCE
                self.health = HunterValue.HEALTH
                self.items = HunterValue.ITEMS
                self.available_item_space = HunterValue.ITEM_CAPACITY
            case AgentRole.CARTOGRAPHER:
                self.agent = Cartographer(name, CartographerValue.GOLD_VISIBILITY_DISTANCE, spawn_position)
                self.gold_visibility_distance = CartographerValue.GOLD_VISIBILITY_DISTANCE
                self.health = CartographerValue.HEALTH
                self.items = CartographerValue.ITEMS
                self.available_item_space = CartographerValue.ITEM_CAPACITY
            case AgentRole.KNIGHT:
                self.agent = Knight(name, KnightValue.GOLD_VISIBILITY_DISTANCE, spawn_position)
                self.gold_visibility_distance = KnightValue.GOLD_VISIBILITY_DISTANCE
                self.health = KnightValue.HEALTH
                self.items = KnightValue.ITEMS
                self.available_item_space = KnightValue.ITEM_CAPACITY
            case AgentRole.BWL_STUDENT:
                self.agent = BWLStudent(name, BWLStudentValue.GOLD_VISIBILITY_DISTANCE, spawn_position)
                self.gold_visibility_distance = BWLStudentValue.GOLD_VISIBILITY_DISTANCE
                self.health = BWLStudentValue.HEALTH
                self.items = BWLStudentValue.ITEMS
                self.available_item_space = BWLStudentValue.ITEM_CAPACITY
        if (self.agent is None or self.gold_visibility_distance is None or self.health is None or
                self.items is None or self.available_item_space is None):
            raise "error creating agent - missing data"

        for item_amount in self.items:
            self.available_item_space -= item_amount
        if self.available_item_space < 0:
            raise "error creating agent - too many items"

    def replenish(self):
        match self.role:
            case AgentRole.KNIGHT:
                if self.health < KnightValue.REPLENISH_HEALTH:
                    self.health += 1
            case AgentRole.HUNTER:
                if self.items[AgentItem.ARROW.value] < HunterValue.REPLENISH_ARROWS and self.available_item_space > 0:
                    self.items[AgentItem.ARROW.value] += 1
                    self.available_item_space -= 1
            case _:
                pass


class DefaultAgentValue:
    HEALTH: int = 1
    ITEM_CAPACITY: int = 5
    GOLD_VISIBILITY_DISTANCE: int = 0
    ITEMS: list[int] = [0] * len(AgentItem)


class HunterValue(DefaultAgentValue):
    ITEMS: list[int] = DefaultAgentValue.ITEMS
    ITEMS[AgentItem.ARROW.value] = 5

    # specifics
    REPLENISH_ARROWS: int = 5


class CartographerValue(DefaultAgentValue):
    pass


class KnightValue(DefaultAgentValue):
    HEALTH: int = 3
    ITEM_CAPACITY: int = 3

    # specifics
    REPLENISH_HEALTH: int = 3


class BWLStudentValue(DefaultAgentValue):
    ITEM_CAPACITY: int = 10
    GOLD_VISIBILITY_DISTANCE: int = 2

from Project.SimulatedAgent.AgentEnums import AgentRole, AgentItem
from Project.Agent.Agent import Agent, Hunter, Cartographer, Knight, BWLStudent
from Project.Environment.TileCondition import TileCondition
import random
from Project.Environment.Map import Map

class SimulatedAgent:
    def __init__(self, name: int, role: AgentRole, spawn_position: tuple[int, int], map_width: int, map_height: int,
                 replenish_time: int, grid: Map):
        self.name: int = name
        self.role: AgentRole = role
        self.position: tuple[int, int] = spawn_position

        self.grid = grid
        self.agent: Agent
        self.health: int
        self.items: list[int]
        self.available_item_space: int
        match role:
            case AgentRole.HUNTER:
                self.agent = Hunter(name, spawn_position, map_width, map_height, replenish_time, grid.info)
                self.health = HunterValue.HEALTH
                self.items = HunterValue.ITEMS
                self.available_item_space = HunterValue.ITEM_CAPACITY
            case AgentRole.CARTOGRAPHER:
                self.agent = Cartographer(name, spawn_position, map_width, map_height, replenish_time, grid.info)
                self.health = CartographerValue.HEALTH
                self.items = CartographerValue.ITEMS
                self.available_item_space = CartographerValue.ITEM_CAPACITY
                self.agent.receive_tiles_with_condition(self.grid.info[TileCondition.WALL.value], TileCondition.WALL)
            case AgentRole.KNIGHT:
                self.agent = Knight(name, spawn_position, map_width, map_height, replenish_time, grid.info)
                self.health = KnightValue.HEALTH
                self.items = KnightValue.ITEMS
                self.available_item_space = KnightValue.ITEM_CAPACITY
            case AgentRole.BWL_STUDENT:
                self.agent = BWLStudent(name, spawn_position, map_width, map_height, replenish_time, grid.info)
                self.health = BWLStudentValue.HEALTH
                self.items = BWLStudentValue.ITEMS
                self.available_item_space = BWLStudentValue.ITEM_CAPACITY

        if self.agent is None or self.health is None or self.items is None or self.available_item_space is None:
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
            case AgentRole.BWL_STUDENT:
                # find all gold positions in reach
                gold_in_reach: list[tuple[int, int]] = []
                max_x: int = min(self.grid.width, self.position[0] + BWLStudentValue.REPLENISH_MAXIMUM_GOLD_DISTANCE + 1)
                min_x: int = max(0, self.position[0] - BWLStudentValue.REPLENISH_MAXIMUM_GOLD_DISTANCE)
                max_y: int = min(self.grid.height, self.position[1] + BWLStudentValue.REPLENISH_MAXIMUM_GOLD_DISTANCE + 1)
                min_y: int = max(0, self.position[1] - BWLStudentValue.REPLENISH_MAXIMUM_GOLD_DISTANCE)
                for x in range(min_x, max_x):
                    for y in range(min_y, max_y):
                        if TileCondition.SHINY in self.grid.get_tile_conditions(x, y):
                            gold_in_reach.append((x, y))
                # randomly choose a gold position in reach
                if gold_in_reach:
                    x, y = random.choice(gold_in_reach)
                    self.agent.receive_gold_position(x, y)
            case _:
                pass

    def get_map(self) -> list[list[set[TileCondition]]]:
        return self.agent.get_map()


class DefaultAgentValue:
    HEALTH: int = 1
    ITEM_CAPACITY: int = 5
    ITEMS: list[int] = [0] * len(AgentItem)


class HunterValue(DefaultAgentValue):
    ITEM_CAPACITY: int = 3
    ITEMS: list[int] = DefaultAgentValue.ITEMS
    ITEMS[AgentItem.ARROW.value] = 1

    # specifics
    REPLENISH_ARROWS: int = 1


class CartographerValue(DefaultAgentValue):
    pass


class KnightValue(DefaultAgentValue):
    HEALTH: int = 2
    ITEM_CAPACITY: int = 3

    # specifics
    REPLENISH_HEALTH: int = 2


class BWLStudentValue(DefaultAgentValue):
    ITEM_CAPACITY: int = 10

    # specifics
    REPLENISH_MAXIMUM_GOLD_DISTANCE: int = 5

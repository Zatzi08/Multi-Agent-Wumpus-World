from Project.Environment.Map import Map
from Project.SimulatedAgent import SimulatedAgent
from Project.Agent.Agent import AgentRole, AgentItem, AgentAction
from Project.Knowledge.KnowledgeBase import TileCondition
from Project.communication.protocol import CommunicationChannel

import random

# constants
REPLENISH_TIME: int = 32

# user input
print("Please input the following things:\n")
MAP_WIDTH: int = int(input("   width of map: "))
print("\n")
MAP_HEIGHT: int = int(input("   height of map: "))
print("\n")
number_of_agents: int = int(input("   number of agents: "))
print("\n")
number_of_simulation_steps: int = int(input("   number of simulation steps: "))
print("\n\n")

# grid/map
grid = Map(MAP_WIDTH, MAP_HEIGHT)

random.seed()

# agents
agents: dict[int, SimulatedAgent] = {}
for i in range(0, number_of_agents, 1):
    spawn_position: tuple[int, int] = random.choice(grid.get_safe_tiles())
    role: AgentRole = random.choice(list(AgentRole))
    agents[i] = SimulatedAgent(i, role, spawn_position, MAP_WIDTH, MAP_HEIGHT)
grid.add_agents(agents)
communication_channel: CommunicationChannel = CommunicationChannel(agents)


# simulate
def agent_move_action(agent: SimulatedAgent, x: int, y: int):
    if TileCondition.WALL in grid.get_tile_conditions(x, y):
        agent.agent.receive_bump_information(x, y)
        return
    elif TileCondition.WUMPUS in grid.get_tile_conditions(x, y):
        if agent.role == AgentRole.KNIGHT:
            grid.delete_condition(x, y, TileCondition.WUMPUS)
        agent.health -= 1
        if agent.health == 0:
            grid.delete_agent(agent.name)
        return
    elif TileCondition.PIT in grid.get_tile_conditions(x, y):
        grid.delete_agent(agent.name)
        agents.pop(agent.name)
        return
    agent.position = (x, y + 1)


def agent_shoot_action(agent: SimulatedAgent, x: int, y: int):
    if agent.items[AgentItem.ARROW.value] > 0:
        agent.items[AgentItem.ARROW.value] -= 1
        agent.available_item_space += 1
    if TileCondition.WUMPUS in grid.get_tile_conditions(x, y):
        grid.delete_condition(x, y, TileCondition.WUMPUS)


# TODO: track goal progress for agents

for i in range(1, number_of_simulation_steps + 1, 1):
    # replenish
    if not i % REPLENISH_TIME:
        for agent in agents.values():
            agent.replenish()

    # give every agent knowledge about their status and the tile they are on
    for agent in agents.values():
        position: tuple[int, int] = agent.position
        conditions: list[TileCondition] = grid.get_tile_conditions(position[0], position[1])
        agent.agent.receive_tile_information(position, i, conditions)

    # give every agent the possibility to establish communication
    for agent in agents.values():
        names_of_agents_in_proximity: list[int] = grid.get_agents_in_reach(i, 1)
        agents_in_proximity: [tuple[int, AgentRole]] = []
        for name in names_of_agents_in_proximity:
            agents_in_proximity.append((name, agents[name].role))
        communication_channel.communicate(agent.name, agents_in_proximity)

    # have every agent perform an action
    for agent in agents.values():
        action: AgentAction = agent.agent.get_next_action()
        x: int = agent.position[0]
        y: int = agent.position[1]
        match action:
            case AgentAction.MOVE_UP:
                agent_move_action(agent, x, y + 1)
            case AgentAction.MOVE_LEFT:
                agent_move_action(agent, x - 1, y)
            case AgentAction.MOVE_RIGHT:
                agent_move_action(agent, x + 1, y)
            case AgentAction.MOVE_DOWN:
                agent_move_action(agent, x, y - 1)
            case AgentAction.PICK_UP:
                if agent.available_item_space > 0 and TileCondition.SHINY in grid.get_tile_conditions(x, y):
                    agent.items[AgentItem.GOLD.value] += 1
                    agent.available_item_space -= 1
                    grid.delete_condition(x, y, TileCondition.SHINY)
            case AgentAction.SHOOT_UP:
                agent_shoot_action(agent, x, y + 1)
            case AgentAction.SHOOT_LEFT:
                agent_shoot_action(agent, x - 1, y)
            case AgentAction.SHOOT_RIGHT:
                agent_shoot_action(agent, x + 1, y)
            case AgentAction.SHOOT_DOWN:
                agent_shoot_action(agent, x, y - 1)
            case AgentAction.SHOUT:
                names_of_agents_in_proximity: list[int] = grid.get_agents_in_reach(agent.name, 3)
                for name in names_of_agents_in_proximity:
                    agents[name].agent.receive_shout_action_information(x, y)

    # TODO get parameters to choose map
    map_is_grid: bool = True
    map_of_agent: int = 0
    if map_is_grid:
        grid.print_map()
    else:
        agent: SimulatedAgent = agents[map_of_agent]
        to_be_printed_map: Map = agent.agent.get_map()
        to_be_printed_map.print_map()

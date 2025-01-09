from Project.Environment.Map import Map
from Project.Agent.Agent import AgentRole, AgentAction, AgentItem, Agent, Hunter, Cartographer, Knight, BWLStudent
from Project.Knowledge.KnowledgeBase import TileCondition
from Project.communication.protocol import startCommunication

import random

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
grid = Map(MAP_HEIGHT, MAP_WIDTH)

random.seed()

# agents
agents: dict[int, Agent] = {}
for i in range(0, number_of_agents, 1):
    spawn_position: tuple[int, int] = random.choice(grid.get_safe_tiles())
    match (random.choice(list(AgentRole))):
        case AgentRole.HUNTER:
            agents[i] = Hunter(i, spawn_position)
        case AgentRole.CARTOGRAPHER:
            agents[i] = Cartographer(i, spawn_position)
        case AgentRole.KNIGHT:
            agents[i] = Knight(i, spawn_position)
        case AgentRole.BWL_STUDENT:
            agents[i] = BWLStudent(i, spawn_position)
grid.add_agents(agents)

# simulate
def agent_move_action(agent: Agent, x: int, y: int):
    if TileCondition.WALL in grid.get_tile_conditions(x, y):
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


def agent_shoot_action(agent: Agent, x: int, y: int):
    if agent.items[AgentItem.ARROW] > 0:
        agent.items[AgentItem.ARROW] -= 1
        agent.current_item_count -= 1
    if TileCondition.WUMPUS in grid.get_tile_conditions(x, y):
        grid.delete_condition(x, y, TileCondition.WUMPUS)


for i in range(1, number_of_simulation_steps+1, 1):
    # give every agent knowledge of the tile they are on
    for _, agent in agents.items():
        position: tuple[int, int] = agent.position
        conditions: list[TileCondition] = grid.get_tile_conditions(position[0], position[1])
        agent.receive_tile_information(position[0], position[1], i, conditions)

    # give every agent the possibility to establish communication
    for _, agent in agents.items():
        names_of_agents_in_proximity: list[int] = grid.get_agents_in_reach(i, 1)
        agents_in_proximity: list[tuple[int, AgentRole]] = []
        for name in names_of_agents_in_proximity:
            agents_in_proximity.append((name, agents[name].role))
        answer: tuple[bool, list[int]] = agent.communicate(agents_in_proximity)

        # check if communication is wanted
        if answer[0]:
            agents_in_communication: list[int] = [agent.name]
            for name in answer[1]:
                answer_to_invite: tuple[bool, list[int]] = agents[name].communicate([(agent.name, agent.role)])
                if answer_to_invite[0]:
                    agents_in_communication.append(name)

            # start communication
            if len(agents_in_communication) > 1:
                startCommunication(agents_in_communication)

    # have every agent perform an action
    for _, agent in agents.items():
        action: AgentAction = agent.get_next_action()
        x: int = agent.position[0]
        y: int = agent.position[1]
        match action:
            case AgentAction.MOVE_UP:
                agent_move_action(agent, x, y+1)
            case AgentAction.MOVE_LEFT:
                agent_move_action(agent, x-1, y)
            case AgentAction.MOVE_RIGHT:
                agent_move_action(agent, x+1, y)
            case AgentAction.MOVE_DOWN:
                agent_move_action(agent, x, y-1)
            case AgentAction.PICK_UP:
                if (agent.current_item_count < agent.item_capacity
                        and TileCondition.SHINY in grid.get_tile_conditions(x, y)):
                    agent.items[AgentItem.GOLD] += 1
                    agent.current_item_count += 1
                    grid.delete_condition(x, y, TileCondition.SHINY)
            case AgentAction.SHOOT_UP:
                agent_shoot_action(agent, x, y+1)
            case AgentAction.SHOOT_LEFT:
                agent_shoot_action(agent, x-1, y)
            case AgentAction.SHOOT_RIGHT:
                agent_shoot_action(agent, x+1, y)
            case AgentAction.SHOOT_DOWN:
                agent_shoot_action(agent, x, y-1)
            case AgentAction.SHOUT:
                names_of_agents_in_proximity: list[int] = grid.get_agents_in_reach(agent.name, 3)
                for name in names_of_agents_in_proximity:
                    agents[name].receive_shout_action_information(x, y)

    # replenish
    REPLENISH_TIMER = 3
    if not i % REPLENISH_TIMER:
        for _, agent in agents.items():
            agent.replenish()

    # print map
    grid.print_map()

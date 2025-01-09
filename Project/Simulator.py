from Project.Environment.Map import Map
from Project.Agent.base_agent import AgentRole, AgentAction, base_agent, hunter, cartographer, knight, bwl_student
from Project.Knowledge.KnowledgeBase import TileCondition

import random

# user input
print("Please input the following things:\n")
map_width: int = int(input("   width of map: "))
print("\n")
map_height: int = int(input("   height of map: "))
print("\n")
number_of_agents: int = int(input("   number of agents: "))
print("\n")
number_of_simulation_steps: int = int(input("   number of simulation steps: "))
print("\n\n")

# grid/map
grid = Map(map_height, map_width, [])

# add agents
agents: dict[int, base_agent] = {}
random.seed()
for i in range(0, number_of_agents, 1):
    match (random.choice(list(AgentRole))):
        case AgentRole.HUNTER:
            agents[i] = hunter(i)
        case AgentRole.CARTOGRAPHER:
            agents[i] = cartographer(i)
        case AgentRole.KNIGHT:
            agents[i] = knight(i)
        case AgentRole.BWL_STUDENT:
            agents[i] = bwl_student(i)
    grid.addAgent(agents[i])

# simulate
for i in range(0, number_of_simulation_steps, 1):
    for _, agent in agents.items():
        position: tuple[int, int] = agent.getPos()
        conditions: list[TileCondition] = grid.getEventsOnTile(position[0], position[1])
        agent.receive_tile_information(position[0], position[1], conditions)

    for _, agent in agents.items():
        names_of_agents_in_proximity: list[int] = grid.getAgentsInReach(i)
        agents_in_proximity: list[tuple[int, AgentRole]] = []
        for agent_name in names_of_agents_in_proximity:
            agents_in_proximity.append((agent_name, agents[agent_name].get_role()))
        agent.communicate(agents_in_proximity)

    for _, agent in agents.items():
        action: AgentAction = agent.getNextAction()
        match (action):
            case AgentAction.MOVE_UP:
            case AgentAction.MOVE_LEFT:
            case AgentAction.MOVE_RIGHT:
            case AgentAction.MOVE_DOWN:
            case AgentAction.SHOOT:

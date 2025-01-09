from Project.Environment.Map import Map
from Project.Agent.base_agent import AgentRole, AgentAction, base_agent, hunter, cartographer, knight, bwl_student
from Project.Knowledge.KnowledgeBase import TileCondition
from Project.communication.protocol import startCommunication

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
    # give every agent knowledge of the tile they are on
    for _, agent in agents.items():
        position: tuple[int, int] = agent.getPos()
        conditions: list[TileCondition] = grid.getEventsOnTile(position[0], position[1])
        agent.receive_tile_information(position[0], position[1], conditions)

    # give every agent the possibility to establish communication
    for _, agent in agents.items():
        names_of_agents_in_proximity: list[int] = grid.getAgentsInReach(i)
        agents_in_proximity: list[tuple[int, AgentRole]] = []
        for name in names_of_agents_in_proximity:
            agents_in_proximity.append((name, agents[name].get_role()))
        answer: tuple[bool, list[int]] = agent.communicate(agents_in_proximity)

        # check if communication is wanted
        if answer[0]:
            agents_in_communication: list[int] = [agent.getName()]
            for name in answer[1]:
                answer_to_invite: tuple[bool, list[int]] = agents[name].communicate(agent.getName())
                if answer_to_invite[0]:
                    agents_in_communication.append(name)

            # start communication
            if len(agents_in_communication) > 1:
                startCommunication(agents_in_communication)

    # have every agent perform an action
    for _, agent in agents.items():
        action: AgentAction = agent.getNextAction()
        match (action):
            case AgentAction.MOVE_UP:
            case AgentAction.MOVE_LEFT:
            case AgentAction.MOVE_RIGHT:
            case AgentAction.MOVE_DOWN:
            case AgentAction.SHOOT:


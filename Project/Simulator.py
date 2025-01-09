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
grid = Map(MAP_HEIGHT, MAP_WIDTH, [])

random.seed()

# add agents
agents: dict[int, Agent] = {}
for i in range(0, number_of_agents, 1):
    spawn_position: tuple[int, int] = random.choice(grid.getSafeTiles())
    match (random.choice(list(AgentRole))):
        case AgentRole.HUNTER:
            agents[i] = Hunter(i, spawn_position)
        case AgentRole.CARTOGRAPHER:
            agents[i] = Cartographer(i, spawn_position)
        case AgentRole.KNIGHT:
            agents[i] = Knight(i, spawn_position)
        case AgentRole.BWL_STUDENT:
            agents[i] = BWLStudent(i, spawn_position)
    grid.addAgent(agents[i], spawn_position)

# simulate
for i in range(0, number_of_simulation_steps, 1):
    # give every agent knowledge of the tile they are on
    for _, agent in agents.items():
        position: tuple[int, int] = agent.position
        conditions: list[TileCondition] = grid.getEventsOnTile(position[0], position[1])
        agent.receive_tile_information(position[0], position[1], conditions)

    # give every agent the possibility to establish communication
    for _, agent in agents.items():
        names_of_agents_in_proximity: list[int] = grid.getAgentsInReach(i)
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
                if TileCondition.WALL in grid.getEventsOnTile(x, y+1):
                    break
                elif TileCondition.WUMPUS in grid.getEventsOnTile(x, y+1):
                    if agent.role == AgentRole.KNIGHT:
                        grid.delete_condition(x, y, TileCondition.WUMPUS)
                    agent.health -= 1
                    if agent.health == 0:
                        grid.deleteAgent(agent.name)
                    break
                elif TileCondition.PIT in grid.getEventsOnTile(x, y+1):
                    grid.deleteAgent(agent.name)
                    break
                agent.position = (x, y+1)
            case AgentAction.MOVE_LEFT:
            case AgentAction.MOVE_RIGHT:
            case AgentAction.MOVE_DOWN:
            case AgentAction.PICK_UP:
            case AgentAction.SHOOT_UP:
            case AgentAction.SHOOT_LEFT:
            case AgentAction.SHOOT_RIGHT:
            case AgentAction.SHOOT_DOWN:
            case AgentAction.SHOUT:

    # replenish
    REPLENISH_TIMER = 3
    if not i % REPLENISH_TIMER:
        for _, agent in agents.items():
            agent.replenish()

    # print map
    grid.printMap()

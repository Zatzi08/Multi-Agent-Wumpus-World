from Project.SimulatedAgent.AgentEnums import AgentGoal
from Project.Simulator import Simulator
import pandas as pd


def single_run_collector(number_of_agents: int = 5, number_of_simulation_steps: int = 200, with_communication: bool = True, seed: int = 123,
                         map_width: int = 30, map_height: int = 30):
    colName = ["Agent", "Role", "Round", "Gold", "Killed_Wumpus", "Map_Progress"]
    dataArray = []
    simulator = Simulator(map_width, map_height, number_of_agents, number_of_simulation_steps, with_communication, seed)
    agents = simulator.get_agents()
    for round in range(1, number_of_simulation_steps):
        _, meta = simulator.simulate_next_step(-1)
        for agent in agents.values():
            dataArray.append([agent.name,
                              agents[agent.name].role.name,
                              round,
                              meta[agent.name][AgentGoal.GOLD.value][0],
                              meta[agent.name][AgentGoal.WUMPUS.value][0],
                              meta[agent.name][AgentGoal.MAP_PROGRESS.value][0]])

    return pd.DataFrame(dataArray, columns=colName)


def multiple_run_result_collector(simulation_count, number_of_agents: int = 5, number_of_simulation_steps: int = 200,
                                  with_communication: bool = True, start_seed: int = 123, map_width: int = 30, map_height: int = 30):
    colName = ["Agent", "Role", "Simulation", "Gold", "Killed_Wumpus", "Map_Progress"]
    dataArray = []
    ss = []
    for simulationID in range(1, simulation_count):
        simulator = Simulator(map_width, map_height, number_of_agents, number_of_simulation_steps, with_communication, start_seed + simulationID)
        print(f"seed: {start_seed + simulationID}")
        for _ in range(1, number_of_simulation_steps - 1):
            _, meta = simulator.simulate_next_step(-1)
        _, meta = simulator.simulate_next_step(-1)
        agents = simulator.get_agents()
        if len(agents) < number_of_agents:
            ss.append(start_seed + simulationID)
        for agent in agents.values():
            dataArray.append([agent,
                              agent.role.name,
                              simulationID,
                              meta[agent.name][AgentGoal.GOLD.value][0],
                              meta[agent.name][AgentGoal.WUMPUS.value][0],
                              meta[agent.name][AgentGoal.MAP_PROGRESS.value][0]])

    return pd.DataFrame(dataArray, columns=colName), ss
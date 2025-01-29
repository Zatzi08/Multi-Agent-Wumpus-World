from Project.SimulatedAgent.AgentEnums import AgentGoal
from Project.Simulator import Simulator
import pandas as pd


def single_run_collector(number_of_agents: int = 5, number_of_simulation_steps: int = 200, seed: int = 123,
                         map_width: int = 30, map_height: int = 30):
    colName = ["Agent", "Role", "Round", "Gold", "Killed_Wumpus", "Nutzungszeitraum"]
    dataArray = []
    simulator = Simulator(map_width, map_height, number_of_agents, number_of_simulation_steps, seed)
    agents = simulator.get_agents()
    for round in range(1, number_of_simulation_steps):
        _, meta = simulator.simulate_next_step(-1)
        for agentName in range(len(meta)):
            dataArray.append([agentName,
                              agents[agentName].role.name,
                              round,
                              meta[agentName][AgentGoal.GOLD.value][0],
                              meta[agentName][AgentGoal.WUMPUS.value][0],
                              meta[agentName][AgentGoal.MAP_PROGRESS.value][0]])

    return pd.DataFrame(dataArray, columns=colName)


def multiple_run_result_collector(simulation_count, number_of_agents: int = 5, number_of_simulation_steps: int = 200,
                                  seed: int = 123, map_width: int = 30, map_height: int = 30):
    colName = ["Agent", "Role", "Simulation", "Gold", "Killed_Wumpus", "Nutzungszeitraum"]
    dataArray = []
    for simulationID in range(1, simulation_count):
        simulator = Simulator(map_width, map_height, number_of_agents, number_of_simulation_steps, seed)
        agents = simulator.get_agents()
        for _ in range(1, number_of_simulation_steps - 1):
            _, meta = simulator.simulate_next_step(-1)
        _, meta = simulator.simulate_next_step(-1)
        for agentName in range(len(meta)):
            dataArray.append([agentName,
                              agents[agentName].role.name,
                              simulationID,
                              meta[agentName][AgentGoal.GOLD.value][0],
                              meta[agentName][AgentGoal.WUMPUS.value][0],
                              meta[agentName][AgentGoal.MAP_PROGRESS.value][0]])

    return pd.DataFrame(dataArray, columns=colName)
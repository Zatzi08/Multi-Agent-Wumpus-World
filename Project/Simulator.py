from Project.Environment.Map import Map, print_random_map
from Project.SimulatedAgent import SimulatedAgent
from Project.Agent.Agent import AgentRole, AgentItem, AgentAction
from Project.Knowledge.KnowledgeBase import TileCondition
from Project.communication.protocol import CommunicationChannel
import random

random.seed()


class Simulator:
    def __init__(self, map_width: int, map_height: int, number_of_agents: int, number_of_simulation_steps: int):
        self.__current_step: int = 0
        self.__number_of_simulation_steps: int = number_of_simulation_steps
        self.__grid: Map = Map(map_width, map_height)
        self.__replenish_time: int = 32
        self.__agents: dict[int, SimulatedAgent] = {}
        self.__set_up_agents(self.__grid.width, self.__grid.height, number_of_agents)
        self.__communication_channel: CommunicationChannel = CommunicationChannel(self.__agents)
        # TODO: track goal progress for agents

    def __set_up_agents(self, map_width: int, map_height: int, number_of_agents: int):
        for i in range(0, number_of_agents, 1):
            spawn_position: tuple[int, int] = random.choice(self.__grid.get_safe_tiles())
            role: AgentRole = random.choice(list(AgentRole))
            self.__agents[i] = SimulatedAgent(i, role, spawn_position, map_width, map_height, self.__replenish_time,
                                              self.__grid)
        self.__grid.add_agents(self.__agents)

    def __agent_move_action(self, agent: int, x: int, y: int):
        if TileCondition.WALL in self.__grid.get_tile_conditions(x, y):
            self.__agents[agent].agent.receive_bump_information(x, y)
            return
        elif TileCondition.WUMPUS in self.__grid.get_tile_conditions(x, y):
            if self.__agents[agent].role == AgentRole.KNIGHT:
                self.__grid.delete_condition(x, y, TileCondition.WUMPUS)
            self.__agents[agent].health -= 1
            if self.__agents[agent].health == 0:
                self.__grid.delete_agent(self.__agents[agent].name)
                del self.__agents[agent]
                return
        elif TileCondition.PIT in self.__grid.get_tile_conditions(x, y):
            self.__grid.delete_agent(self.__agents[agent].name)
            del self.__agents[agent]
            return
        self.__agents[agent].position = (x, y)

    def __agent_shoot_action(self, agent: int, x: int, y: int):
        if self.__agents[agent].items[AgentItem.ARROW.value] > 0:
            self.__agents[agent].items[AgentItem.ARROW.value] -= 1
            self.__agents[agent].available_item_space += 1
        if TileCondition.WUMPUS in self.__grid.get_tile_conditions(x, y):
            self.__grid.delete_condition(x, y, TileCondition.WUMPUS)

    def get_agents(self):
        return self.__agents

    def print_map(self, view):
        if view < 0 or view >= len(self.__agents):
            return self.__grid.print_map()
        else:
            return print_random_map(self.__agents[view].agent.get_map(), self.__grid.width, self.__grid.height, self.__agents[view])

    def simulate_next_step(self, view: int):
        print("\nstep:", self.__current_step)
        current_step = self.__current_step
        if self.__current_step == self.__number_of_simulation_steps:
            return
        self.__current_step += 1

        # replenish
        if not self.__current_step % self.__replenish_time:
            for agent in self.__agents.values():
                self.__agents[agent.name].replenish()

        # give every agent knowledge about their status and the tile they are on
        for agent in self.__agents.values():
            conditions: list[TileCondition] = self.__grid.get_tile_conditions(self.__agents[agent.name].position[0],
                                                                              self.__agents[agent.name].position[1])
            name = agent.name
            self.__agents[agent.name].agent.receive_tile_information(self.__agents[agent.name].position, conditions,
                                                                     self.__agents[agent.name].health,
                                                                     self.__agents[agent.name].items,
                                                                     self.__agents[agent.name].available_item_space,
                                                                     self.__current_step)

        # give every agent the possibility to establish communication
        """for agent in self.__agents.values():
            names_of_agents_in_proximity: list[int] = self.__grid.get_agents_in_reach(self.__agents[agent.name].name, 1)
            agents_in_proximity: [tuple[int, AgentRole]] = []
            for name in names_of_agents_in_proximity:
                agents_in_proximity.append((name, self.__agents[name].role))
            self.__communication_channel.communicate(agent.name, agents_in_proximity)"""

        # have every agent perform an action
        agent_list: list[int] = list(self.__agents.keys())
        for agent in agent_list:
            name = self.__agents[agent].name
            if name == 3 and current_step == 5:
                print(self.__agents[agent].agent.get_map()[self.__agents[agent].position[1]][self.__agents[agent].position[0]])
            action: AgentAction = self.__agents[agent].agent.get_next_action()
            print(name, action.name)
            x: int = self.__agents[agent].position[0]
            y: int = self.__agents[agent].position[1]
            match action:
                case AgentAction.MOVE_RIGHT:
                    self.__agent_move_action(self.__agents[agent].name, x + 1, y)
                case AgentAction.MOVE_UP:
                    self.__agent_move_action(self.__agents[agent].name, x, y + 1)
                case AgentAction.MOVE_DOWN:
                    self.__agent_move_action(self.__agents[agent].name, x, y - 1)
                case AgentAction.MOVE_LEFT:
                    self.__agent_move_action(self.__agents[agent].name, x - 1, y)
                case AgentAction.PICK_UP:
                    if self.__agents[agent].available_item_space > 0 and TileCondition.SHINY in self.__grid.get_tile_conditions(x, y):
                        self.__agents[agent].items[AgentItem.GOLD.value] += 1
                        self.__agents[agent].available_item_space -= 1
                        self.__grid.delete_condition(x, y, TileCondition.SHINY)
                case AgentAction.SHOOT_RIGHT:
                    self.__agent_shoot_action(self.__agents[agent].name, x + 1, y)
                case AgentAction.SHOOT_UP:
                    self.__agent_shoot_action(self.__agents[agent].name, x, y + 1)
                case AgentAction.SHOOT_DOWN:
                    self.__agent_shoot_action(self.__agents[agent].name, x, y - 1)
                case AgentAction.SHOOT_LEFT:
                    self.__agent_shoot_action(self.__agents[agent].name, x - 1, y)
                case AgentAction.SHOUT:
                    names_of_agents_in_proximity: list[int] = self.__grid.get_agents_in_reach(self.__agents[agent].name, 3)
                    for name in names_of_agents_in_proximity:
                        self.__agents[name].agent.receive_shout_action_information(x, y)

        if self.__current_step == self.__number_of_simulation_steps:
            print("Simulation done.")

        # return simulation view
        self.__grid.add_agents(self.__agents)
        return self.print_map(view)
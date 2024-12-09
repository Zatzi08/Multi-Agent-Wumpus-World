from Project.Simulator import Map
from Project.Knowledge.KnowledgeBase import KnowledgeBase
import numpy

class base_agent():
    def __init__(self, name, health, items, goal, position, map_width, map_height):
        self.name = name
        self.health = health
        self.items = items
        self.goal = goal
        self.gold_capacity = 5
        self.knowledge = KnowledgeBase(name, map_width, map_height, position)
        self.visibility_range = 0
        self.gold_visibility_range = 0
        self.position = (1, 1)

    def move(self, direction):  #soll ich das zu einer Liste von Agenten machen, wenn ein Team irgendwo hin will?
        width = Map.shape[0]
        height = Map.shape[1]
        x, y = self.position
        directions = {
            "up": (x, y + 1),
            "down": (x, y - 1),
            "right": (x + 1, y),
            "left": (x - 1, y)
        }
        new_x, new_y = directions[direction]

        if 0 < new_x < height and 0 < new_y < width:
            if 2 in Map[new_y][new_x]:  #wenn keine wand (enum oder list idk)
                print("Invalid move!")

            # Wumpus oderso
            elif 4 in Map[new_y][new_x]:
                if "shield" in self.items and self.health > 1:
                    self.health -= 1
                elif "swordsman" in Map[new_y][new_x]:  #swordsman ist im team
                    pass
                else:
                    self.agentDeath()
            #pit
            elif 7 in Map[new_y][new_x]:
                self.agentDeath()

            #gold:wenn ein team auf gold ist, wer kriegt das gold dann?
            elif 10 in Map[new_y][new_x]:
                if self.items.count("gold") < self.gold_capacity: #soll gold in items oder in eigenem counter sein?
                    self.items.append("gold")

            #update knowledge base?

            self.position = new_x, new_y
            return self.position


    #check pit and wumpus in move: arrow or sword? -> call methods

    def shoot(self, direction):
        if "Arrow" in self.items and self.items[1] > 0: #kriegt jeder jetzt pfeile? range erstmal auf 3 gesetzt
            x, y = self.position
            ranges = {
                "up": [(x,y+1),(x,y+2),(x,y+3)],
                "down": [(x,y-1),(x,y-2),(x,y-3)],
                "right": [(x+1,y),(x+2,y),(x+3,y)],
                "left": [(x-1,y),(x-2,y),(x-3,y)]
            }

            self.checkShoot(ranges[direction])

        else:
            print(self.name, "has no arrows left!")
        #if wall or wumpus then stop flying oder kann man 2 töten?

    def checkShoot(self, positions):
        for pos in positions:
            if 0 < pos[0] < Map.shape[0] and 0 < pos[1] < Map.shape[1]:
                if 2 in Map[pos[1]][pos[0]]:
                    index = Map[pos[1]][pos[0]].index(2)
                    Map[pos[1]][pos[0]].pop(index)
                    print(self.name, "has killed a Wumpus!")
                    #break ?
                elif 1 in Map[pos[1]][pos[0]]:
                    break



    def agentDeath(self):
        self.health = 0
        #lösche agent aus karte
        index = Map[self.position[1]][self.position[0]].index(self.name)
        Map[self.position[1]][self.position[0]].pop(index)
        print(self.name, "has died!")


class hunter(base_agent):
    def __init__(self, name, health):  #Bogen als Item?
        super().__init__(name, health, [["Arrow", 5]], ["wumpus"])


class cartographer(base_agent):
    def __init__(self, name, health):  #Karte als Item?
        super().__init__(name, health, [], ["map"])

    def init_knowledge(self, knowledge):  #alle haben ja theoretisch knowledge, nicht?
        self.knowledge = knowledge


class knight(base_agent):
    def __init__(self, name, health):  #Schwert und Schild als Items?
        super().__init__(name, health, [["sword", 1], ["shield", 1]], ["gold", "wumpus"])


class bwl_student(base_agent):
    def __init__(self, name, health):  #Sack als Item?
        super().__init__(name, health, [], ["gold"])
        self.gold_capacity = 10
        self.gold_visibility_range = 3

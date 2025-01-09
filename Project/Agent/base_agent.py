from Project.Simulator import Map
from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
import numpy


class base_agent():
    HUNTER_ARROW = 5
    DEFAULT_HEALTH = 1
    KNIGHT_HEALTH = 3
    REPLENISH_TIME = 3

    def __init__(self, name, health, items, goal, position, map_width, map_height):
        self.name = name
        self.health = base_agent.DEFAULT_HEALTH
        self.items = items
        self.goal = goal
        self.gold_capacity = 5
        self.gold_count = 0
        self.knowledge = KnowledgeBase(name, map_width, map_height, position)
        self.visibility_range = 0
        self.gold_visibility_range = 0
        self.position = (1, 1)
        self.roundcount = 0

    def getName(self):
        return self.name

    def move(self, direction):
        height = Map.shape[0]
        width = Map.shape[1]
        x, y = self.position
        directions = {
            "up": (x, y + 1),
            "down": (x, y - 1),
            "right": (x + 1, y),
            "left": (x - 1, y)
        }
        new_x, new_y = directions[direction]

        if 0 < new_x < width and 0 < new_y < height:
            if TileCondition.WALL in Map[new_y][
                new_x]:  #wenn keine wand (enum oder list idk) TODO: gute Frage... wahrscheinlich werden alle Infos aus der KB genommen, aber vielleicht nochmal fragen
                # TODO: also wahrscheinlich Enum
                print("Invalid move!")

            # Wumpus oderso
            elif TileCondition.WUMPUS in Map[new_y][new_x]:
                if "shield" in self.items and self.health > 1:
                    self.health -= 1

                elif "swordsman" in Map[new_y][
                    new_x]:  #swordsman ist im team TODO: Entweder ist swordsman einfach zuerst dran oder man macht aktion -> death -> move
                    pass


                else:
                    map.deleteAgent(self.name)

            #pit
            elif TileCondition.PIT in Map[new_y][new_x]:
                map.deleteAgent(self.name)


            #gold:wenn ein team auf gold ist, wer kriegt das gold dann? TODO: Jeder Agent für sich. Erster mit leerem Beutel oder Vote (kann diskutiert werden)
            elif TileCondition.SHINY in Map[new_y][new_x]:
                if self.gold_count < self.gold_capacity:
                    Map.deleteCondition(self, x, y, TileCondition.SHINY)
                    self.gold_count += 1

            self.position = new_x, new_y
            return self.position

    def shoot(self, direction):
        if "Arrow" in self.items and self.items[1] > 0:
            # TODO: friendly fire?
            x, y = self.position
            inAir = True
            directions = {
                "up": {"x": 0, "y": 1},
                "down": {"x": 0, "y": -1},
                "right": {"x": 1, "y": 0},
                "left": {"x": -1, "y": 0}
            }

            while inAir and (0 < x < Map.shape[1] and 0 < y < Map.shape[0]):
                x += directions[direction][x]
                y += directions[direction][y]
                if TileCondition.SAFE not in Map[y][x]:
                    if TileCondition.WUMPUS in Map[y][x]:
                        #remove Wumpus from list
                        Map.deleteCondition(self, x, y, TileCondition.WUMPUS)
                        break

                    elif TileCondition.WALL:
                        inAir = False
                        break

                    #TODO: elif TileCondition.AGENT: -> wird ein Bündnis zwischen den Agenten gemacht?
                    #pass

        else:
            print(self.name, "has no arrows left!")


def checkReplenish(self, name, item):
    #check if a hunter arrow has already been used
    if name == "hunter":
        if self.item[1] < base_agent.HUNTER_ARROW:
            if self.roundcount == base_agent.REPLENISH_TIME:
                self.item[1] += 1
            else:
                self.roundcount += 1

    #check if health is already lost
    elif name == "knight":
        if self.health < base_agent.KNIGHT_HEALTH:
            if self.roundcount == base_agent.REPLENISH_TIME:
                self.health += 1
            self.roundcount += 1


# reload Method?
# karte zeichnen Method? TODO: Sollte Knowledge-Base sein, also Kartograf wird einfach mit mehr Wissen initialisiert

class hunter(base_agent):
    def __init__(self, name, health):  #Bogen als Item?
        super().__init__(name, health, [["Arrow", base_agent.HUNTER_ARROW]], ["wumpus"])


class cartographer(base_agent):
    def __init__(self, name, health):  #Karte als Item?
        super().__init__(name, health, ["map", 1], ["map"])

    def init_knowledge(self, knowledge):  #alle haben ja theoretisch knowledge, nicht?
        self.knowledge = knowledge


class knight(base_agent):
    def __init__(self, name, health):  #Schwert und Schild als Items?
        super().__init__(name, health, [["sword", 1], ["shield", 1]], ["gold", "wumpus"])
        self.health = base_agent.KNIGHT_HEALTH


class bwl_student(base_agent):
    def __init__(self, name, health):  #Sack als Item?
        super().__init__(name, health, [], ["gold"])
        self.gold_capacity = 10
        self.gold_visibility_range = 3

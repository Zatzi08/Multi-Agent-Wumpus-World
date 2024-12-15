from Project.Simulator import Map
from Project.Knowledge.KnowledgeBase import KnowledgeBase, TileCondition
import numpy


class base_agent():
    def __init__(self, name, health, items, goal, position, map_width, map_height):
        self.name = name
        self.health = health
        self.items = items
        self.goal = goal
        self.gold_capacity = 5
        self.gold_count = 0
        self.knowledge = KnowledgeBase(name, map_width, map_height, position)
        self.visibility_range = 0
        self.gold_visibility_range = 0
        self.position = (1, 1)

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
                    new_x]:  #swordsman ist im team TODO: Eigentlich ist jeder Agent für sich du musst also nur einen allgemeinen Move machen, denke ich
                    pass


                else:
                    self.agentDeath()

            #pit
            elif TileCondition.PIT in Map[new_y][new_x]:
                self.agentDeath()


            #gold:wenn ein team auf gold ist, wer kriegt das gold dann? TODO: Jeder Agent für sich. Erster mit leerem Beutel oder Vote (kann diskutiert werden)
            elif TileCondition.SHINY in Map[new_y][new_x]:
                if self.gold_count < self.gold_capacity:
                    self.gold_count += 1

            #gold:wenn ein team auf gold ist, wer kriegt das gold dann?
            elif 10 in Map[new_y][new_x]:
                if self.items.count("gold") < self.gold_capacity:  #soll gold in items oder in eigenem counter sein?
                    self.items.append("gold")

            #update knowledge base? TODO: ja

            self.position = new_x, new_y
            return self.position

    def agentDeath(self):
        x, y = self.position
        self.health = 0
        # lösche agent aus karte
        index = Map[y][x].index(self.name)  # wie wird ein Agent auf einer bestimmten Position gespeichert?
        Map[y][x].pop(index)
        print(self.name, "has died!")

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
                        index = Map[y][x].index(TileCondition.WUMPUS)
                        Map[y][x].pop(index)
                        print(self.name, "has killed a Wumpus!")
                        inAir = False
                        break

                    elif TileCondition.WALL:
                        inAir = False
                        break

                    #elif TileCondition.AGENT:
                    #pass

        else:
            print(self.name, "has no arrows left!")

        #hat swordsman eine Reichweite zum Nachbarsfeld?

    #check pit and wumpus in move: arrow or sword? -> call methods

    def shoot(self, direction):
        if "Arrow" in self.items and self.items[1] > 0:  #kriegt jeder jetzt pfeile? range erstmal auf 3 gesetzt
            xPos, yPos = self.position
            directions = {
                "up": {"x": 0, "y": 1},
                "down": {"x": 0, "y": -1},
                "right": {"x": 1, "y": 1},
                "left": {"x": -1, "y": 0}
            }

            for pos in directions[direction]:  #hier code beendet
                if 0 < pos[0] < Map.shape[0] and 0 < pos[1] < Map.shape[1]:
                    if 2 in Map[pos[1]][pos[0]]:
                        index = Map[pos[1]][pos[0]].index(2)
                        Map[pos[1]][pos[0]].pop(index)
                        print(self.name, "has killed a Wumpus!")
                        # break ?
                    elif 1 in Map[pos[1]][pos[0]]:
                        break


        else:
            print(self.name, "has no arrows left!")


#reload Method?
#karte zeichnen Method?

class hunter(base_agent):
    def __init__(self, name, health):  #Bogen als Item?
        super().__init__(name, health, [["Arrow", 5]], ["wumpus"])


class cartographer(base_agent):
    def __init__(self, name, health):  #Karte als Item?
        super().__init__(name, health, ["map", 1], ["map"])

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

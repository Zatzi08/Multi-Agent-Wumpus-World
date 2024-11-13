class base_agent():
    def __init__(self,name,health, items, goal):
        self.name = name
        self.health = health
        self.items = items
        self.goal = goal
        self.gold_capacity = 5
        self.knowledge = []
        self.visibility_range = 0
        self.gold_visibility_range = 0
class hunter(base_agent):
    def __int__(self,name,health):#Bogen als Item?
        super().__init__(name, health, [["Arrow", 5]], ["wumpus"])
class cartographer(base_agent):
    def __int__(self,name,health): #Karte als Item?
        super().__init__(name, health, [],["map"])

    def init_knowledge(self, knowledge):
        self.knowledge = knowledge

class scout(base_agent):
    def __int__(self,name,health):#Fernglas als Item?
        super().__init__(name,health,[], ["gold"])
        self.visibility_range = 1

class knight(base_agent):
    def __init__(self,name,health):#Schwert und Schild als Items?
        super().__init__(name, health, [["sword",1],["shield",1]], ["gold", "wumpus"])

class bwl_student(base_agent):
    def __init__(self,name, health):#Sack als Item?
        super().__init__(name,health, [], ["gold"])
        self.gold_capacity = 10
        self.gold_visibility_range = 3



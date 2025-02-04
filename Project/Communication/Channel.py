from Project.SimulatedAgent.AgentEnums import AgentItem, AgentRole
from Project.Communication.Offer import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject
from Project.Environment.TileCondition import TileCondition
import random


class Channel:
    def __init__(self, agents):
        self.agents = agents
        self.initiator: int = 0  # set for each Communication
        self.participants: [int] = []  # set for each Communication

    def set_agents(self, agents):
        self.agents = agents

    # initiator: tuple[int, AgentRole]
    def communicate(self, initiator, potential_receivers, step) -> bool:
        request_type = self.agents[initiator].agent.get_offer_type()
        receivers: list[int] = self.agents[initiator].agent.start_communication(potential_receivers, request_type)
        #print(f"initiator in comm: {initiator}, receivers in comm: {receivers}")


        # check if Communication should take place
        if not receivers:
            #print(f"{initiator} found no receivers")
            return False

        # set sender and receivers
        self.initiator = initiator
        self.participants = receivers

        # TODO create offer from offered_objects and requested_objects

        receiver_answers: dict[int, tuple[ResponseType, OfferedObjects, RequestedObjects, int]] = {}

        # for each participant: get answer to offer, answer_to_offer -> tuple[ResponseType, OfferedObjects, RequestedObjects]
        desired_tiles = set()
        acceptable_tiles = set()
        knowledge_tiles = self.agents[initiator].agent.knowledge_tiles()
        gold_amount = self.agents[initiator].items[AgentItem.GOLD.value]
        wumpus_amount = 0
        if request_type == RequestObject.TILE_INFORMATION:
            desired_tiles = self.agents[initiator].agent.desired_tiles()
            acceptable_tiles = self.agents[initiator].agent.acceptable_tiles(desired_tiles)
        if request_type == RequestObject.KILL_WUMPUS:
            wumpus_amount = len(self.agents[initiator].agent.get_knowledgebase().get_tiles_by_condition(TileCondition.WUMPUS))
        for participant in self.participants:
            receiver_answers.update(
                {participant: self.agents[participant].agent.answer_to_offer(request_type, desired_tiles, acceptable_tiles, knowledge_tiles, gold_amount, wumpus_amount)})
            #print(f"receiver: {participant}, answer: ({receiver_answers[participant][0].name}, {receiver_answers[participant][1]}, {receiver_answers[participant][2]})")

        if not receiver_answers:
            #print("No answers!")
            return False
        # put all accepting answers and counter-offers into new dicts
        accepted_requests: dict[int, tuple[OfferedObjects, RequestedObjects, int]] = {}
        for participant, p_answer in receiver_answers.items():
            if p_answer[0] == ResponseType.ACCEPT:
                # verify_offer(p_answer[1], participant) # soll verify_offer was returnen oder geht das so?
                accepted_requests.update({participant: (p_answer[1], p_answer[2], p_answer[3])})

        # get best offer out of accepted and counteroffers
        best_utility = -2
        best_offer, best_utility = self.get_best_offer(accepted_requests, initiator, best_utility)

        if best_offer is not None:
            #print(f"best offer: Offer: {best_offer[1]} | Request: {best_offer[2]} with utility: {best_utility} from {best_offer[0]}")
            pass

        #print(f"[CFP] {best_offer.keys()} offers: {best_offer.values()} for the request {list(best_offer.values())[0][1]}") TODO: Fix

        # if every offer is bad, negotiate with everyone who has accepted the request or gave a counteroffer
        if best_utility < -1:
            #print(f"Sender received only bad offers. Starting negotiation!")
            receiver_offers: dict[int, Offer] = {}
            for participant, offer in accepted_requests.items():
                receiver_offer: Offer = Offer(offer[0], offer[1], self.agents[participant].role)
                receiver_offers.update({participant: receiver_offer})

            self.start_negotiation(initiator, receiver_offers)

        # finish Communication (distribute offered objects)
        else:
            receiver = best_offer[0]
            #print(f"The request is completed, with {best_offer} as the accepted offer")
            self.apply_changes(initiator, receiver, best_offer[2], best_offer[1])
            return True

    def apply_changes(self, initiator: int, receiver: int, receiver_request: RequestedObjects,
                      receiver_offer: OfferedObjects):
        """applies all changes to the associated agents after a successful Communication process"""
        # changes in simulated agents
        # change to requested objects, getter for the request stuff
        if receiver_request.gold != 0:
            self.agents[receiver].items[AgentItem.GOLD.value] += receiver_request.gold
            self.agents[receiver].agent.change_gold_amount(receiver_request.gold)
            self.agents[initiator].items[AgentItem.GOLD.value] -= receiver_request.gold
            self.agents[initiator].agent.change_gold_amount(-receiver_request.gold)

        if receiver_offer.gold_amount != 0:
            self.agents[initiator].items[AgentItem.GOLD.value] += receiver_offer.gold_amount
            self.agents[initiator].agent.change_gold_amount(receiver_offer.gold_amount)
            self.agents[receiver].items[AgentItem.GOLD.value] -= receiver_offer.gold_amount
            self.agents[receiver].agent.change_gold_amount(-receiver_offer.gold_amount)

        if receiver_request.tiles:
            for (x, y) in receiver_request.tiles:
                self.agents[receiver].agent.receive_tile_from_communication(x, y, self.agents[
                    initiator].agent.return_tile_conditions(x, y))

        if receiver_offer.tile_information:
            for (x, y, conditions) in receiver_offer.tile_information:
                self.agents[initiator].agent.receive_tile_from_communication(x, y, set(conditions))

        if receiver_request.wumpus_positions != 0:
            pos = self.agents[initiator].agent.receive_found_wumpus()
            a = list(pos)[:receiver_request.wumpus_positions]

            for (x, y) in a:
                self.agents[receiver].agent.add_kill_wumpus_task(x, y)

        if receiver_offer.wumpus_positions != 0:
            pos = self.agents[receiver].agent.receive_found_wumpus()
            a = list(pos)[:len(receiver_offer.wumpus_positions)]

            for (x, y) in a:
                self.agents[initiator].agent.add_kill_wumpus_task(x, y)

    def get_best_offer(self, offer_list: dict[int, tuple[OfferedObjects, RequestedObjects, int]], sender: int,
                        best_utility: int):
        best_offer = None
        if len(offer_list) >= 1:
            for participant, p_answer in offer_list.items():
                offer_utility = self.agents[sender].agent.evaluate_offer(p_answer[0], p_answer[1], p_answer[2])
                #print(f"Offer utility: {offer_utility}, best utility: {best_utility}")
                if offer_utility > best_utility or best_offer is None:
                    best_utility = offer_utility
                    best_offer = (participant, p_answer[0], p_answer[1])

                # choose randomly if two offers have same utility
                elif offer_utility == best_utility:
                    rand = random.choice([0, 1])
                    if rand == 0:
                        best_utility = offer_utility
                        best_offer = (participant, p_answer[0], p_answer[1])

        else:
            #print(f"Everyone denied the offer from {sender}.")
            pass

        return best_offer, best_utility

    def start_negotiation(self, initiator: int, receivers: dict[int: Offer]):
        # the sender has constant request, the receivers are changing their offer to fit the sender
        negotiation_round = 0
        limit = 3
        good_offers: dict[int, tuple[OfferedObjects,RequestedObjects, int]] = {}
        best_utility = -2
        best_offer: tuple[int, OfferedObjects, RequestedObjects] = None
        desired_tiles = self.agents[initiator].agent.desired_tiles()
        acceptable_tiles = self.agents[initiator].agent.acceptable_tiles(desired_tiles)
        #print("A negotiation has started!")
        while negotiation_round < limit:
            negotiation_round += 1
            for participant, offer in receivers.copy().items():
                p_agent = self.agents[participant].agent
                #print("Type of agent: " + str(type(p_agent)))
                counter_offer, counter_request, desired_tiles_amount = p_agent.create_counter_offer(offer, desired_tiles,acceptable_tiles)
                # verify_offer(counter_offer, participant)
                if counter_offer is None:
                    #print(f"Counteroffer from {participant} is None, leaving")
                    del receivers[participant]
                    continue
                receivers[participant] = Offer(counter_offer, counter_request, self.agents[initiator].role)
                #print("Evaluate utility:", self.agents[initiator].agent.evaluate_offer(counter_offer, counter_request, desired_tiles_amount), "for counteroffer", counter_offer, counter_request)
                if self.agents[initiator].agent.evaluate_offer(counter_offer, counter_request, desired_tiles_amount) >= -1:
                    good_offers.update({participant: (counter_offer, counter_request, desired_tiles_amount)})


            if len(good_offers) > 0:
                #print("Good offers are found, looking for the best")
                best_offer, best_utility= self.get_best_offer(good_offers, initiator, best_utility)
                break

        if best_offer is not None:
            #print(f"The negotiation has reached an agreement with offer: {best_offer[1]} and request {best_offer[2]} from {best_offer[0]}")
            receiver = best_offer[0]

            self.apply_changes(initiator, receiver, best_offer[2], best_offer[1])

        else:
            #print(f"The negotiation has failed")
            pass


'''
def verify_offer(self, offer: OfferedObjects, participant: int):
    if offer.gold_amount > self.agents[participant].__items[AgentItem.GOLD.value]:
        offer.gold_amount = self.agents[participant].__items[AgentItem.GOLD.value]

    knowledge = self.agents[participant].__knowledge
    for tile in offer.tile_information.copy():# copy?
        # tile_information[2] ist eine list, get_map.. ist ein set. Wie soll ich das vergleichen? Soll ich tile_information in ein set machen?
        if not (self.agents[participant].return_map[tile[0]][tile[1]]) and self.agents[participant].return_map[tile[0]][tile[1]] == offer.tile_information[2]:
            offer.tile_information.remove(tile)

    for tile in offer.wumpus_positions.copy():# copy?
        # tile_information[2] ist eine list, get_map.. ist ein set. Wie soll ich das vergleichen? Soll ich tile_information in ein set machen?
        if not (self.agents[participant].return_map[tile[0]][tile[1]]) and knowledge.get_condition_of_tile(tile[0], tile[1]) == self.agents[participant].return_map[tile[0]][tile[1]]:
            offer.tile_information.remove(tile)
'''

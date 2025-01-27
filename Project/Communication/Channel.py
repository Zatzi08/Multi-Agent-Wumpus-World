from Project.SimulatedAgent.AgentEnums import AgentItem
from Project.Communication.Offer import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject
import random

class Channel:  # TODO: Sollte der Kanal nicht den state speichern; eventuell performativ "confirm" zwischen Kanal und initiator zum prüfen ob Wert von Gegenangebot und Content passt
    def __init__(self, agents):
        self.agents = agents
        self.initiator: int = 0  # set for each Communication
        self.participants: [int] = []  # set for each Communication

    def set_agents(self, agents):
        self.agents = agents

#initiator: tuple[int, AgentRole]
    def communicate(self, initiator, potential_receivers) -> bool:
        answer: tuple[list[int], tuple[OfferedObjects, RequestedObjects]] = (
            self.agents[initiator].agent.start_communication(potential_receivers))
        receivers: list[int] = answer[0]
        offered_objects: OfferedObjects = answer[1][0]
        requested_objects: RequestedObjects = answer[1][1]

        # check if Communication should take place
        if not receivers:
            return False

        # set sender and receivers
        self.initiator = initiator
        self.participants = receivers

        # TODO create offer from offered_objects and requested_objects

        initiator_offer: Offer = Offer(offered_objects, requested_objects, initiator[1])

        receiver_answers: dict[int, tuple[ResponseType, OfferedObjects, RequestedObjects]] = {}

        # for each participant: get answer to offer, answer_to_offer -> tuple[ResponseType, OfferedObjects, RequestedObjects]
        for participant in self.participants:
            receiver_answers: dict[int, tuple]
            receiver_answers.update(
                {str(participant): self.agents[participant].agent.answer_to_offer(self.initiator, requested_objects)})

        # TODO evaluate answers
        if not receiver_answers:
            return False
        # put all accepting answers and counter-offers into new dicts
        accepted_requests = dict[int, tuple[OfferedObjects, RequestedObjects]]
        for participant, p_answer in receiver_answers.items():
            if p_answer[0] == ResponseType.ACCEPT:
                verify_offer(p_answer[1], participant) # soll verify_offer was returnen oder geht das so?
                accepted_requests.update({participant: p_answer})
            

        # get best offer out of accepted and counteroffers
        best_utility = -1
        best_offer: dict[int, tuple[OfferedObjects, RequestedObjects]] = {}
        best_offer, best_utility = get_best_offer(accepted_requests, initiator[0], best_offer, best_utility)
        

        print(
            f"[CFP] {best_offer.keys()} offers: {best_offer.values()} for the request {next(iter(best_offer.values()))[1]}")

        # if every offer is bad, negotiate with everyone who has accepted the request or gave a counteroffer
        if best_utility == -1:
            print(f"Sender received only bad offers. Starting negotiation!")
            receiver_offers: dict[int: Offer]
            for participant, offer in accepted_requests.items():
                receiver_offer: Offer = Offer(offer[0], offer[1], self.agents[participant].agent.AgentRole)
                receiver_offers.update({participant: receiver_offer})


            self.agents[initiator[0]].agent.start_negotiation(initiator[0], receiver_offers)
            # return
        # finish Communication (distribute offered objects)
        else:
            receiver = list(best_offer.keys()) #doch next(iter..) nutezn damit das ein int ist?
            offer_answer = list(best_offer.values()) #falscher type?
            print(f"The request is completed, with {best_offer} as the accepted offer")
            self.agents[receiver].agent.apply_changes(initiator[0], receiver, offer_answer[0][1], offer_answer[0][0])
            return True

    def apply_changes(self, sender: int, receiver: int, sender_request: RequestedObjects, sender_offer: OfferedObjects):
        """applies all changes to the associated agents after a successful Communication process"""
        # changes in simulated agents
        # change to requested objects, getter for the request stuff
        if sender_request.gold_amount != 0:
            self.agents[sender].items[AgentItem.GOLD.value] += sender_request.gold_amount

        if sender_offer.gold_amount != 0:
            self.agents[receiver].items[AgentItem.GOLD.value] += sender_offer.gold_amount

        if sender_request.tile_information is not []:
            for (x, y, conditions) in sender_offer.tile_information:
                self.agents[sender].agent.receive_tile_from_communication(x, y, conditions)

        if sender_offer.tile_information is not []:
            for (x, y, conditions) in sender_request.tile_information:
                self.agents[receiver].agent.receive_tile_from_communication(x, y, conditions)

        if sender_request.wumpus_positions is not []:
            for (x, y) in sender_offer.wumpus_positions:
                self.agents[sender].agent.add_kill_wumpus_task(x, y)

        if sender_offer.wumpus_positions is not []:
            for (x, y) in sender_request.wumpus_positions:
                self.agents[receiver].agent.add_kill_wumpus_task(x, y)


def get_best_offer(offer_list: dict[int:tuple[OfferedObjects, RequestedObjects]], sender:int, best_offer: dict[int: tuple[OfferedObjects, RequestedObjects]], best_utility: int):
    if len(offer_list) >= 1:
        for participant, p_answer in offer_list.items():
            offer_utility = sender.evaluate_offer(p_answer[1], p_answer[2])
            if offer_utility > best_utility:
                best_utility = offer_utility
                best_offer = {participant: (p_answer[1], p_answer[2])}
            
            # choose randomly if two offers have same utility
            elif offer_utility == best_utility:
                rand = random.choice([0,1])
                if rand == 0:
                    best_utility = offer_utility
                    best_offer = {participant: (p_answer[1], p_answer[2])}
                
                


    else:
        print(f"Everyone denied the offer from {sender}.")

    return best_offer, best_utility

def start_negotiation(self, initiator: int, receivers: dict[int: Offer]):
    # the sender has constant request, the receivers are changing their offer to fit the sender
    negotiation_round = 0
    limit = 3
    good_offers: dict[int: Offer] = {}
    best_utility = -1
    best_offer: dict[int, tuple[OfferedObjects, RequestedObjects]] = {}

    print("A negotiation has started!")
    while negotiation_round < limit:
        negotiation_round += 1
        for participant, offer in receivers.items():
            p_agent = self.agents[participant].agent
            desired_tiles = p_agent.desired_tiles()
            counter_offer, counter_request = p_agent.create_counter_offer(offer, desired_tiles, p_agent.accepted_tiles(desired_tiles), p_agent.knowledge_tiles(), p_agent.__items[AgentItem.GOLD.value], p_agent.get_wumpus_count())
            verify_offer(counter_offer, participant)
            if self.agents[participant].agent.evaluate_offer() > -1:
                good_offers.update({participant: (counter_offer, counter_request)})

        if len(good_offers) > 0:
            print("Good offers are found, looking for the best")
            best_offer = get_best_offer(good_offers, initiator, best_offer, best_utility)
            break

    if best_offer:
        print(f"The negotiation has reached an agreement with offer: {best_offer.values()} from {best_offer.keys()}")
        receiver = next(iter(best_offer))
        p_offer = next(iter(best_offer))[0]
        p_request = next(iter(best_offer))[1]
        self.agents[participant].agent.apply_changes(initiator, receiver, p_offer, p_request)

    else:
        print(f"The negotiation has failed")

def verify_offer(self, offer: OfferedObjects, participant: int):
    if offer.gold_amount > self.agents[participant].__items[AgentItem.GOLD.value]:
        offer.gold_amount = self.agents[participant].__items[AgentItem.GOLD.value]

    knowledge = self.agents[participant].__knowledge
    for tile in offer.tile_information.copy():# copy?
        # tile_information[2] ist eine list, get_map.. ist ein set. Wie soll ich das vergleichen? Soll ich tile_information in ein set machen?
        if not (self.agents[participant].get_map[tile[0]][tile[1]]) and self.agents[participant].get_map[tile[0]][tile[1]] == offer.tile_information[2]:
            offer.tile_information.remove(tile)

    for tile in offer.wumpus_positions.copy():# copy?
        # tile_information[2] ist eine list, get_map.. ist ein set. Wie soll ich das vergleichen? Soll ich tile_information in ein set machen?
        if not (self.agents[participant].get_map[tile[0]][tile[1]]) and knowledge.get_condition_of_tile(tile[0], tile[1]) == self.agents[participant].get_map[tile[0]][tile[1]]:
            offer.tile_information.remove(tile)

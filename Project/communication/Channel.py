from Project.SimulatedAgent.AgentEnums import AgentItem
from Project.Communication.Offer import Offer, OfferedObjects, RequestedObjects, ResponseType, RequestObject

class Channel:  # TODO: Sollte der Kanal nicht den state speichern; eventuell performativ "confirm" zwischen Kanal und initiator zum prüfen ob Wert von Gegenangebot und Content passt
    def __init__(self, agents):
        self.agents = agents
        self.initiator: int = 0  # set for each communication
        self.participants: [int] = []  # set for each communication

    def set_agents(self, agents):
        self.agents = agents

    def communicate(self, sender, potential_receivers) -> bool:
        answer: tuple[list[int], tuple[OfferedObjects, RequestedObjects]] = (
            self.agents[sender].agent.start_communication(potential_receivers))
        receivers: list[int] = answer[0]
        offered_objects: OfferedObjects = answer[1][0]
        requested_objects: RequestedObjects = answer[1][1]

        # check if communication should take place
        if not receivers:
            return False

        # set sender and receivers
        self.initiator = sender
        self.participants = receivers

        # TODO create offer from offered_objects and requested_objects

        initiator_offer: Offer = Offer(offered_objects, requested_objects, sender[1])

        receiver_answers: dict[int, tuple[ResponseType, OfferedObjects, RequestedObjects]] = {}

        # for each participant: get answer to offer, answer_to_offer -> tuple[ResponseType, OfferedObjects, RequestedObjects]
        for participant in self.participants:
            receiver_answers: dict[int, tuple]
            receiver_answers.update(
                {str(participant): self.agents[participant].agent.answer_to_offer(self.initiator, initiator_offer)})

        # TODO evaluate answers
        if not receiver_answers:
            return False
        # put all accepting answers and counter-offers into new dicts
        accepted_requests = dict[int, tuple[OfferedObjects, RequestedObjects]]
        counter_offers = dict[int, tuple[OfferedObjects, RequestedObjects]]
        for participant, p_answer in receiver_answers.items():
            if p_answer[0] == ResponseType.ACCEPT:
                accepted_requests.update({participant: p_answer})
            elif p_answer[0] == ResponseType.COUNTEROFFER:
                counter_offers.update({participant: p_answer})

        # get best offer out of accepted and counteroffers
        best_utility = -1
        best_offer: dict[int, tuple[OfferedObjects, RequestedObjects]] = {}
        best_offer, best_utility = get_best_offer(accepted_requests, sender, best_offer, best_utility)
        best_offer, best_utility = get_best_offer(counter_offers, sender, best_offer, best_utility)

        print(
            f"[CFP] {best_offer.keys()} offers: {best_offer.values()} for the request {next(iter(best_offer.values()))[1]}")

        # if every offer is bad, negotiate with everyone who has accepted the request or gave a counteroffer
        if best_utility == -1:
            print(f"Sender received only bad offers. Starting negotiation!")
            self.agents[sender].agent.start_negotiation(sender, potential_receivers, initiator_offer)
            # return
        # finish communication (distribute offered objects)
        else:
            receiver = best_offer.keys()
            offer_answer = best_offer.values()
            print(f"The request is completed, with {best_offer} as the accepted offer")
            self.agents[receiver].agent.apply_changes(sender, receiver, next(iter(offer_answer))[1], next(iter(offer_answer))[0])
            return True

    def apply_changes(self, sender: int, receiver: int, receiver_offer: OfferedObjects, sender_offer: OfferedObjects):
        """applies all changes to the associated agents after a successful communication process"""
        # changes in simulated agents
        if receiver_offer.gold_amount != 0:
            self.agents[sender].items[AgentItem.GOLD.value] += receiver_offer.gold_amount

        if sender_offer.gold_amount != 0:
            self.agents[receiver].items[AgentItem.GOLD.value] += sender_offer.gold_amount

        if receiver_offer.tile_information is not []:
            for (x, y, conditions) in sender_offer.tile_information:
                self.agents[sender].agent.receive_tile_from_communication(x, y, conditions)

        if sender_offer.tile_information is not []:
            for (x, y, conditions) in receiver_offer.tile_information:
                self.agents[receiver].agent.receive_tile_from_communication(x, y, conditions)

        if receiver_offer.wumpus_positions is not []:
            for (x, y) in sender_offer.wumpus_positions:
                self.agents[sender].agent.add_kill_wumpus_task(x, y)

        if sender_offer.wumpus_positions is not []:
            for (x, y) in receiver_offer.wumpus_positions:
                self.agents[receiver].agent.add_kill_wumpus_task(x, y)

# TODO: fühlt sich mehr an wie Funktionen des Kanals so wie es geschrieben ist
# Eventueller Ablauf von kommunikation:
#   - Initiator initialisiert Kanal mit Sender, Receiver, Request, usw.
#   - Kanal übernimmt kommunikation bis Ergebnis vorhanden
#   - Kanal setzt Ergebnis um (an Agent)

# wenn mehrere agenten auf einem Feld sind wird Kommunikation gestartet
# abfragen, ob mit gleichem Agenten schonmal kommuniziert wurde


# simulator ruft das auf, nicht utility da utility von kommunikation aufgerufen wird nicht andersrum (man kommuniziert immer)

def get_best_offer(offer_list: dict[int:tuple[OfferedObjects, RequestedObjects]], sender, best_offer, best_utility):
    if len(offer_list) >= 1:
        for participant, p_answer in offer_list.items():
            offer_utility = sender.evaluate_offer(p_answer[1], p_answer[2])
            if offer_utility > best_utility:
                best_utility = offer_utility
                best_offer = {participant: (p_answer[1], p_answer[2])}


    else:
        print(f"Everyone denied the offer from {sender}.")

    return best_offer, best_utility

def start_negotiation(self, receivers: list[int], initiator_offer):
    # the sender has constant request, the receivers are changing their offer to fit the sender
    negotiation_round = 0
    limit = 3
    good_offers: dict[int: Offer] = {}
    best_utility = -1
    best_offer: dict[int, tuple[OfferedObjects, RequestedObjects]] = {}

    print("A negotiation has started!")
    while negotiation_round < limit:
        negotiation_round += 1
        # for participant in receivers:
            # offer = self.agents[participant].agent.create_counter_offer(initiator_offer,
                                                                        # self.agents[participant].agent.desired_tiles(initiator_offer.req_tiles),
                                                                        # self.agents[participant].agent.accepted_tiles(initiator_offer.req_tiles),)
            # if self.agents[participant].agent.evaluate_offer() > -1:
                # good_offers.update({participant: offer})

        if len(good_offers) > 0:
            print("Good offers are found, looking for the best")
            for participant, offer in good_offers.items():
                offer_utility = self.agents[participant].evaluate_offer(self, offer[0], offer[1])
                if offer_utility > best_utility:
                    best_utility = offer_utility
                    best_offer = {participant: (offer[0], offer[1])}

            break

    if best_offer:
        print(f"The negotiation has reached an agreement with offer: {best_offer.values()} from {best_offer.keys()}")

    else:
        print(f"The negotiation has failed")

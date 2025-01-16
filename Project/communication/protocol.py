from enum import Enum
from typing import List, Union, Optional
from Project.Agent.Agent import *
from Project.Environment import Map
from Project.SimulatedAgent import SimulatedAgent

class Performative(Enum):
    CFP = 1
    REQUEST = 2
    RESPONSE = 3
    INFORM = 4


class RequestObject(Enum):
    GOLD = 1
    TILE_INFORMATION = 2
    KILL_WUMPUS = 3

class ResponseType(Enum):
    ACCEPT = 1
    DENY = 2
    COUNTEROFFER = 3


class OfferedObjects:
    def __init__(self, gold_amount: int, tile_information: list[tuple[int, int, list[TileCondition]]], wumpus_positions: [tuple[int, int]]):
        self.gold_amount = gold_amount
        self.tile_information = tile_information
        self.wumpus_positions = wumpus_positions

class RequestedObjects:
    def __init__(self, gold: int, tiles: list[tuple[int, int]], wumpus_positions: int):
        self.gold: int = gold
        self.tiles: list[tuple[int, int]] = tiles
        self.wumpus_positions: int = wumpus_positions

class Offer:
    def __init__(self, offered_objects: OfferedObjects, requested_objects: RequestedObjects):
        # TODO create offer from OfferedObjects and RequestedObjects
        pass

# TODO: warum nicht obj in Message init? Wahrscheinlich useless
class Message:
    def __init__(self,
                 performative: Performative,
                 sender: str,
                 receiver: Union[str, List[str]],
                 content: dict[RequestObject, Union[str, int, tuple]],
                 obj: Union[RequestObject, RequestObject]):
        self.performative = performative
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.obj = obj

    def __repr__(self):
        return f"Message(performative={self.performative}, obj={self.obj}, sender={self.sender}, " \
               f"receiver={self.receiver}, content={self.content})"

class CommunicationChannel:  # TODO: Sollte der Kanal nicht den state speichern; eventuell performativ "confirm" zwischen Kanal und initiator zum prüfen ob Wert von Gegenangebot und Content passt
    def __init__(self, agents: dict[int, SimulatedAgent]):
        self.agents = agents
        self.initiator: int = 0 # set for each communication
        self.participants: [int] = [] # set for each communication

    def set_agents(self, agents: dict[int, SimulatedAgent]):
        self.agents = agents

    def communicate(self, sender: int, potential_receivers: [int, AgentRole]) -> None:
        answer: tuple[list[int], tuple[OfferedObjects, RequestedObjects]] = self.agents[sender].agent.start_communication(potential_receivers)
        receivers: list[int] = answer[0]
        offered_objects: OfferedObjects = answer[1][0]

        # check if communication should take place
        if not receivers:
            return
        # TODO handle verification of offered objects/maybe keep the verified parts instead of breaking communication
        if not verify_offered_objects(offered_objects):
            return

        # set sender and receivers
        self.initiator = sender
        self.participants = receivers

        # set requested objects
        requested_objects: RequestedObjects = answer[1][1]


        # TODO create offer from offered_objects and requested_objects
        offer: Offer = Offer(offered_objects, requested_objects)

        # for each participant: get answer to offer
        for participant in self.participants:
            self.agents[participant].agent.answer_to_offer(self.initiator, offer)

        # TODO evaluate answers

        # TODO finish communication (distribute offered objects)

# TODO: fühlt sich mehr an wie Funktionen des Kanals so wie es geschrieben ist
# Eventueller Ablauf von kommunikation:
#   - Initiator initialisiert Kanal mit Sender, Receiver, Request, usw.
#   - Kanal übernimmt kommunikation bis Ergebnis vorhanden
#   - Kanal setzt Ergebnis um (an Agent)

#wenn mehrere agenten auf einem Feld sind wird Kommunikation gestartet
#abfragen, ob mit gleichem Agenten schonmal kommuniziert wurde

# bwler würde gold verlangen, um Position zu geben
# knight würde für help gold verlangen

def verify_offered_objects(offer_objects: OfferedObjects) -> bool:
    # TODO check if an offer is valid
    return False



#simulator ruft das auf, nicht utility da utility von kommunikation aufgerufen wird nicht andersrum (man kommuniziert immer)
def handle_request(sender, receiver, request_type: RequestObject, offer):
    response = utility.calcResponse(sender,receiver, request_type, offer) #response (Status, Objekt) oderso TODO: utility über Agent aufrufen
    if response[0] == Status.ACCEPT:
        print(f"[Request] {receiver.name} accepted the request.")
        
        #ist das Angebot Gold, Position oder Help? TODO: offer Objekt nutzen
        if offer[0] = "gold":
            #remove gold
            return [position]

        elif offer[0] = "position":
            #schicke dem anderen irgendwie position idk
            return [position]

        return [position]
    
    elif response[0] == COUNTEROFFER:
        negotiation(sender, receiver, request_type, offer, counteroffer: response[1])
    
    else:
        print(f"[Request] {receiver.name} denied the request.")
        return None

#TODO: das dann in utility
#def calcResponse(sender, receiver, request_type: RequestTypeObj, offer):
    #return (status, object)

def handle_request(sender, receiver, request_type: RequestTypeObj, counteroffer):
    print(f"[Request] {sender.name} sent request to {receiver.name}: {request_type}, Counteroffer: {counteroffer}")
    response = receiver.respond_to_request(request_type, counteroffer)
    print(f"[Request] {receiver.name} responded with: {response}")

    if response.get(RequestTypeObj.STATUS) == ResponseType.ACCEPT:
        print(f"[Request] {receiver.name} accepted the request.")
        sender.fulfill_request(receiver, request_type)
        receiver.fulfill_request(sender, counteroffer)
    else:
        print(f"[Request] {receiver.name} denied the request.")


def handle_cfp(sender, participants, cfp_type: RequestTypeObj):
    print(f"[CFP] {sender.name} broadcasted CFP for: {cfp_type}")
    responses = []

    for participant in participants:
        response = participant.respond_to_cfp(cfp_type)
        responses.append((participant, response))
        print(f"[CFP] {participant.name} responded with: {response}")

    best_offer = None
    for participant, response in responses:
        if response.get(RequestTypeObj.STATUS) == ResponseType.ACCEPT and \
                (best_offer is None or response.get(RequestTypeObj.COUNTEROFFER < best_offer.get(RequestTypeObj.COUNTEROFFER))):
            best_offer = response
            best_participant = participant

    if best_offer:
        print(f"[CFP] {sender.name} accepted the offer from {best_participant.name}: {best_offer}")
        #return fulfill request oderso [bestp, sender_price, receiver_price]
    else:
        print("[CFP] No acceptable offer received.")

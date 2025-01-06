from enum import Enum
from typing import List, Union, Optional
from Project.Agent.base_agent import *
from Project.Environment import Map


class Performative(Enum):
    CFP = 1
    REQUEST = 2
    RESPONSE = 3
    INFORMATION = 4


# TODO: Frage: Was genau ist Content Key? Unterschied Help und Request?
class ContentKey(Enum):
    POSITION = 1
    COUNTEROFFER = 2
    HELP = 3
    STATUS = 4


class Status(Enum):
    ACCEPT = 1
    DENY = 2


# TODO: Warum kein allgemeines Offer Enum mit GOLD, KNOWDLEDGE, REQUEST ?
class CounterOffer(Enum):
    GOLD = 1
    REQUEST = 2

# TODO: warum nicht obj in Message init?
class Message:
    def __init__(self,
                 performative: Performative,
                 sender: str,
                 receiver: Union[str, List[str]],
                 content: dict[ContentKey, Union[str, int, tuple]]):
        self.performative = performative
        self.sender = sender
        self.receiver = receiver
        self.content = content

    def __repr__(self):  # TODO: Warum ist hier ein "obj" drin, aber nicht in der Klasse
        return f"Message(performative={self.performative}, obj={self.obj}, sender={self.sender}, " \
               f"receiver={self.receiver}, content={self.content})"


# Kommunikationskanal
class CommunicationChannel:  # TODO: Sollte der Kanal nicht den state speichern; eventuell performativ "confirm" zwischen Kanal und initiator zum prüfen ob Wert von Gegenangebot und Content passt
    def __init__(self, initiator, participants,
                 map_instance: Map):  # TODO: Warum benötigtest du hier die Map. Solltest doch einfach davon ausgehen können, dass participants valid sind
        self.initiator = initiator
        self.participants = self.filter_neighbors(initiator, participants, map_instance) # TODO: kann man mit den Nachbarn kommunizieren? Dachte nur auf gleichem Feld
        self.completed = False

        if not self.participants:
            raise ValueError(f"No neighbors in range for {initiator.name}. Communication not possible.")

        print(f"[Channel] Initialized with participants: {[p.name for p in self.participants]}")

    def filter_neighbors(self, initiator, participants, map_instance: Map):
        x, y = initiator.position
        neighbors = map_instance.getAgentInReach(x, y)
        valid_participants = [p for p in participants if p in neighbors]
        return valid_participants

    def send_direct(self, sender, recipient, message: Message):
        print(f"[Channel] {sender.name} sent direct message to {recipient.name}: {message}")
        recipient.receive_message(message)  # TODO: Sollte der Responce nicht gespeichert/zurückgeben werden oder so?

    def broadcast(self, message: Message):
        print(f"[Channel] {message.sender} broadcasted: {message}")
        for participant in self.participants:
            participant.receive_message(message)

    def close(self):
        print(
            f"[Channel] Communication between {self.initiator.name} and {len(self.participants)} participants closed.")
        self.completed = True


# TODO: fühlt sich mehr an wie Funktionen des Kanals so wie es geschrieben ist
# Eventueller Ablauf von kommunikation:
#   - Initiator initialisiert Kanal mit Sender, Receiver, Request, usw.
#   - Kanal übernimmt kommunikation bis Ergebnis vorhanden
#   - Kanal gibt Ergebnis an Initiator zurück

def handle_request(sender, receiver, request_type: ContentKey, counteroffer):
    print(f"[Request] {sender.name} sent request to {receiver.name}: {request_type}, Counteroffer: {counteroffer}")
    response = receiver.respond_to_request(request_type, counteroffer)
    print(f"[Request] {receiver.name} responded with: {response}")

    if response.get(ContentKey.STATUS) == Status.ACCEPT:
        print(f"[Request] {receiver.name} accepted the request.")
        sender.fulfill_request(receiver, request_type)
        receiver.fulfill_request(sender, counteroffer)
    else:
        print(f"[Request] {receiver.name} denied the request.")


def handle_cfp(sender, participants, cfp_type: ContentKey):
    print(f"[CFP] {sender.name} broadcasted CFP for: {cfp_type}")
    responses = []

    for participant in participants:
        response = participant.respond_to_cfp(cfp_type)
        responses.append((participant, response))
        print(f"[CFP] {participant.name} responded with: {response}")

    best_offer = None
    for participant, response in responses:
        if response.get(ContentKey.STATUS) == Status.ACCEPT and \
                (best_offer is None or response.get(ContentKey.COUNTEROFFER < best_offer.get(ContentKey.COUNTEROFFER))):
            best_offer = response
            best_participant = participant

    if best_offer:
        print(f"[CFP] {sender.name} accepted the offer from {best_participant.name}: {best_offer}")
        # Logik
    else:
        print("[CFP] No acceptable offer received.")

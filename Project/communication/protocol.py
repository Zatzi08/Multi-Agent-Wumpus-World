from enum import Enum
from typing import List, Union, Optional
from Project.Agent.base_agent import *
from Project.Environment import Map


class Performative(Enum):
    CFP = 1
    REQUEST = 2
    RESPONSE = 3
    COUNTEROFFER = 4
    INFORMATION = 5


class RequestTypeObj(Enum):
    POSITION = 1
    HELP = 2


class ResponseType(Enum):
    ACCEPT = 1
    DENY = 2
    COUNTEROFFER = 3


class CounterOfferObj(Enum):
    GOLD = 1
    HELP = 2
    POSITION = 3

# TODO: warum nicht obj in Message init?
class Message:
    def __init__(self,
                 performative: Performative,
                 sender: str,
                 receiver: Union[str, List[str]],
                 content: dict[RequestTypeObj, Union[str, int, tuple]],
                 obj: Union[RequestTypeObj, CounterOfferObj]):
        self.performative = performative
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.obj = obj

    def __repr__(self):
        return f"Message(performative={self.performative}, obj={self.obj}, sender={self.sender}, " \
               f"receiver={self.receiver}, content={self.content})"


# Kommunikationskanal
class CommunicationChannel:  # TODO: Sollte der Kanal nicht den state speichern; eventuell performativ "confirm" zwischen Kanal und initiator zum prüfen ob Wert von Gegenangebot und Content passt
    def __init__(self, initiator, participants,
                 map_instance: Map):  # TODO: Warum benötigtest du hier die Map. Solltest doch einfach davon ausgehen können, dass participants valid sind
        self.initiator = initiator
        self.participants = participants # TODO: kann man mit den Nachbarn kommunizieren? Dachte nur auf gleichem Feld
        self.completed = False

        if not self.participants:
            raise ValueError(f"No neighbors in range for {initiator.name}. Communication not possible.")

        print(f"[Channel] Initialized with participants: {[p.name for p in self.participants]}")

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
        # Logik
    else:
        print("[CFP] No acceptable offer received.")

import logging
from typing import Optional
from MQTT_packets import CONNECT, SUBSCRIBE, PINGREQ, DISCONNECT, UNSUBSCRIBE, PUBLISH

# Konfigurera loggning
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def route_packet(incoming_packet: dict, client_id: str) -> Optional[bytes]:
    packet_type = incoming_packet.get('Packet type')

    if packet_type == "CONNECT":
        outgoing_packet = CONNECT.handle(incoming_packet, client_id)
    elif packet_type == "DISCONNECT":
        # DISCONNECT hanteras utan att generera ett svarspaket
        DISCONNECT.handle(client_id)
        outgoing_packet = None
    elif packet_type == "SUBSCRIBE":
        outgoing_packet = SUBSCRIBE.handle(incoming_packet, client_id)
    elif packet_type == "UNSUBSCRIBE":
        outgoing_packet = UNSUBSCRIBE.handle(incoming_packet, client_id)
    elif packet_type == "PINGQREQ":
        outgoing_packet = PINGREQ.handle(client_id)
    elif packet_type == "PUBLISH":
        outgoing_packet = PUBLISH.handle(incoming_packet, client_id)
    else:
        logging.error("Unknown packet type: %s. Packet: %s", packet_type, incoming_packet)
        raise ValueError(f"Unknown packet type: {packet_type}")

    return outgoing_packet

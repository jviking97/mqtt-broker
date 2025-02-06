import logging
from MQTT_packets import UNSUBACK
import MQTT_database

# Konfigurera loggning
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def handle(incoming_packet: dict, client_id: str) -> bytes:
    # Hämta packet identifier, topics och flaggor
    packet_identifier = incoming_packet.get('Packet identifier')
    topics = incoming_packet.get('Topics')
    flags = incoming_packet.get('Flags')

    # Kontrollera att flaggorna är korrekta, annars kasta ett undantag
    if flags != "0010":
        logging.error(f"Malformed packet: Expected flags '0010', got '{flags}'.")
        raise ValueError("Malformed packet: Incorrect flags.")

    # Ta bort topics från klientens session
    for topic in topics:
        MQTT_database.session_remove_topic(client_id, topic)
        logging.info(f"Client ID ({client_id}) unsubscribed to ({topic}).")

    # Skapa och returnera UNSUBACK-paketet
    outgoing_packet = UNSUBACK.encode(packet_identifier)
    return outgoing_packet


def decode(data: bytes) -> dict:
    decoded_packet = {}
    current_byte = 0

    # Kontrollera att vi har minst 2 bytes för packet identifiern
    if len(data) < current_byte + 2:
        raise ValueError("Data missing to decode packet identifier.")

    # Avkoda packet identifier (2 bytes)
    packet_identifier_value = int.from_bytes(data[current_byte:current_byte + 2],
                                             byteorder="big")
    decoded_packet['Packet identifier'] = packet_identifier_value
    current_byte += 2

    topics = []
    # Avkoda topics. Läs så länge det finns minst 2 bytes kvar för att läsa topic-längden.
    while current_byte + 2 <= len(data):
        # Läs ut topic filter längd (2 bytes)
        topic_length_value = int.from_bytes(data[current_byte:current_byte + 2],
                                            byteorder="big")
        current_byte += 2

        # Kontrollera att det finns tillräckligt med data för topic filter
        if current_byte + topic_length_value > len(data):
            logging.warning("Not enough data to decode a topic filter; aborting...")
            break

        # Avkoda topic filter
        topic_name = data[current_byte:current_byte + topic_length_value].decode()
        current_byte += topic_length_value
        topics.append(topic_name)

    decoded_packet['Topics'] = topics
    return decoded_packet

import logging
from MQTT_packets import SUBACK
import MQTT_database

# Konfigurera logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def handle(incoming_packet: dict, client_id: str) -> bytes:
    # Hämta packet identifier, topics och flaggor
    packet_identifier = incoming_packet.get('Packet identifier')
    topics = incoming_packet.get('Topics')
    flags = incoming_packet.get('Flags')

    # Kontrollera flaggorna; om de inte är korrekta kastas ett undantag
    if flags != "0010":
        logging.error("Felaktigt paket: Flagga är inte '0010'.")
        raise ValueError("Felaktigt paket: Flagga är inte '0010'.")

    # Om session inte finns, returnera failure-koder för samtliga topics
    if not MQTT_database.session_exists(client_id):
        return_codes = ["10000000" for _ in topics]  # Failure
        return SUBACK.encode(packet_identifier, return_codes)

    # Utvärdera topic-önskemål
    return_codes = []
    for topic in topics:
        # Varje topic antas vara en dict med topic-namnet som nyckel
        topic_name = next(iter(topic))
        if not MQTT_database.topic_exists(topic_name):
            return_codes.append("10000000")  # Failure
        else:
            MQTT_database.session_add_topic(client_id, topic_name)
            logging.info(f"Client ID ({client_id}) subscribed to ({topic_name}).")
            return_codes.append("00000000")  # QoS 0

    # Skapa och returnera SUBACK-paketet
    return SUBACK.encode(packet_identifier, return_codes)


def decode(data: bytes) -> dict:
    decoded_packet = {}
    current_byte = 0

    # Kontrollera att vi har minst 2 bytes för packet identifiern
    if len(data) < 2:
        raise ValueError("Data för kort för att innehålla ett packet identifier.")

    # Avkoda packet identifier (2 bytes)
    packet_identifier_bits = f"{data[current_byte]:08b}{data[current_byte + 1]:08b}"
    packet_identifier_value = int(packet_identifier_bits, 2)
    decoded_packet['Packet identifier'] = packet_identifier_value
    current_byte += 2

    topics = []

    # Medan det finns tillräckligt med data kvar för att läsa ett topic (minst 6 bytes)
    while current_byte + 6 <= len(data):
        # Läs ut topic filter längd (2 bytes)
        topic_filter_length_bits = f"{data[current_byte]:08b}{data[current_byte + 1]:08b}"
        topic_filter_length_value = int(topic_filter_length_bits, 2)
        current_byte += 2

        # Kontrollera att vi har tillräckligt med data för topic filter
        if current_byte + topic_filter_length_value > len(data):
            logging.error("Data saknas för att läsa topic filter.")
            break

        # Läs ut topic filter
        topic_filter_bytes = data[current_byte:current_byte + topic_filter_length_value]
        try:
            topic_filter = topic_filter_bytes.decode()
        except Exception as e:
            logging.error(f"Misslyckades att avkoda topic filter: {e}")
            topic_filter = ""
        current_byte += topic_filter_length_value

        # Läs ut Requested QoS (1 byte)
        if current_byte >= len(data):
            logging.error("Data saknas för att läsa Requested QoS.")
            break
        # Här kan vi direkt använda värdet eftersom det är en byte
        requested_qos_value = data[current_byte]
        current_byte += 1

        topics.append({topic_filter: requested_qos_value})

    decoded_packet['Topics'] = topics
    return decoded_packet
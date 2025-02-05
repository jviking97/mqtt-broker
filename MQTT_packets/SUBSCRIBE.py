from MQTT_packets import SUBACK
import MQTT_database
import sys

def handle(incoming_packet: dict, client_ID: str):

    # Get packet identifier
    packet_identifier = incoming_packet.get('Packet identifier')

    # Get topics
    topics = incoming_packet.get('Topics')

    # Get flags
    flags = incoming_packet.get('Flags')
    if flags != "0010": # Malformed packet
        sys.exit()

    # Check that session exists
    if MQTT_database.session_exists(client_ID) == False:
        return_codes = []
        for _ in topics:
            return_codes.append("10000000")    # Failure
        return SUBACK.encode(packet_identifier, return_codes)

    # Evaluate topic requests
    return_codes = []
    for topic in topics:
        topic_name = next(iter(topic))
        if not MQTT_database.topic_exists(topic_name):
            return_codes.append("10000000")    # Failure
        else:
            # Add subscription to client
            MQTT_database.session_add_topic(client_ID, topic_name)
            print(f'Client ID ({client_ID}) subscribed to ({topic_name})')
            return_codes.append("00000000")   # QoS 0

    # Create packet
    outgoing_packet = SUBACK.encode(packet_identifier, return_codes)
    return outgoing_packet

def decode(bytes):

    # Buffer to hold decoded values from packet
    decoded_packet = {}

    # Control variable
    current_byte = 0

    # Packet identifier
    packet_identifier_bytes_1 = bytes[current_byte]
    packet_identifier_bits_1 = format(packet_identifier_bytes_1, "08b")
    current_byte += 1
    packet_identifier_bytes_2 = bytes[current_byte]
    packet_identifier_bits_2 = format(packet_identifier_bytes_2, "08b")
    current_byte += 1
    packet_identifier_bits = (
        packet_identifier_bits_1 + packet_identifier_bits_2
    )
    packet_identifier_value = int(packet_identifier_bits, 2)
    decoded_packet['Packet identifier'] = packet_identifier_value

    ### PAYLOAD

    # Local storage for topics
    topics = []

    # While we have at least 6 bytes ahead of us
    while current_byte+6 <= len(bytes):

        # Topic filter length
        topic_filter_length_bytes_1 = bytes[current_byte]
        topic_filter_length_bits_1 = format(topic_filter_length_bytes_1, "08b")
        current_byte += 1
        topic_filter_length_bytes_2 = bytes[current_byte]
        topic_filter_length_bits_2 = format(topic_filter_length_bytes_2, "08b")
        current_byte += 1
        topic_filter_length_bits = (
            topic_filter_length_bits_1 + topic_filter_length_bits_2
        )
        topic_filter_length_value = int(topic_filter_length_bits, 2)

        # Topic filter
        topic_filter_bytes = bytes[current_byte:current_byte+topic_filter_length_value]
        topic_filter = topic_filter_bytes.decode()
        current_byte += topic_filter_length_value

        # Requested QoS
        requested_qos_bytes = bytes[current_byte]
        requested_qos_bits = format(requested_qos_bytes, "08b")
        requested_qos_value = int(requested_qos_bits, 2)
        current_byte += 1

        topic = {
            topic_filter : requested_qos_value
        }

        topics.append(topic)
        
    decoded_packet['Topics'] = topics

    return decoded_packet

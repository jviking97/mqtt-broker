from MQTT_packets import UNSUBACK
import MQTT_database
import sys

def handle(incoming_packet: dict, client_ID):

    # Get packet identifier
    packet_identifier = incoming_packet.get('Packet identifier')

    # Get topics
    topics = incoming_packet.get('Topics')

    # Get flags
    flags = incoming_packet.get('Flags')
    if flags != "0010": # Malformed packet
        sys.exit()

    # remove topics from client
    for topic in topics:
        MQTT_database.session_remove_topic(client_ID, topic)
        print(f'Client ID ({client_ID}) unsubscribed to ({topic})')

    # create packet
    outgoing_packet = UNSUBACK.encode(packet_identifier)
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
    while current_byte+5 <= len(bytes):


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
        topic_name = topic_filter_bytes.decode()
        current_byte += topic_filter_length_value
        topics.append(topic_name)
        
    decoded_packet['Topics'] = topics

    return decoded_packet
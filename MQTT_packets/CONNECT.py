import logging
from MQTT_packets import CONNACK
import MQTT_database

# Konfigurera loggning
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def handle(incoming_packet: dict, client_id: str) -> bytes:
    # Hämta protokollnamnet och kontrollera att det är korrekt
    protocol_name = incoming_packet.get('Protocol name')
    if protocol_name != 'MQTT4':
        logging.error(f"Ogiltigt protokoll: {protocol_name}. Förväntat 'MQTT4'.")
        return CONNACK.encode(session_present=False, return_code=1)

    # Extrahera klient-ID från payload; antag att det är det första ordet
    extracted_client_id = incoming_packet.get('Payload').split(' ', 1)[0]
    clean_session = incoming_packet.get('Clean Session flag')

    if clean_session:
        # Vid clean session raderas eventuell gammal session och en ny skapas
        if MQTT_database.session_exists(extracted_client_id):
            MQTT_database.session_delete(extracted_client_id)
        MQTT_database.session_create(extracted_client_id)
        outgoing_packet = CONNACK.encode(session_present=False, return_code=0)
    else:
        # Vid icke clean session kontrolleras om sessionen finns
        if MQTT_database.session_exists(extracted_client_id):
            outgoing_packet = CONNACK.encode(session_present=True, return_code=0)
        else:
            outgoing_packet = CONNACK.encode(session_present=False, return_code=0)

    logging.info(f"Client ID ({client_id}) connected.")
    return outgoing_packet


def decode(data: bytes) -> dict:
    decoded_packet = {}
    current_byte = 0

    # Avkoda längden på protokollnamnet (2 bytes)
    if len(data) < 2:
        raise ValueError("Data för kort för att avkoda protokollnamnets längd.")

    protocol_name_length_bits = f"{data[current_byte]:08b}{data[current_byte + 1]:08b}"
    protocol_name_length_value = int(protocol_name_length_bits, 2)
    decoded_packet["Length of protocol name"] = protocol_name_length_value
    current_byte += 2

    # Avkoda protokollnamnet
    # Ursprungskoden läser (protocol_name_length_value + 1) bytes – kontrollera att detta stämmer med protokollet.
    if current_byte + protocol_name_length_value + 1 > len(data):
        raise ValueError("Data för kort för att avkoda protokollnamnet.")
    protocol_name_bytes = data[current_byte: current_byte + protocol_name_length_value + 1]
    protocol_name_list = []
    for byte in protocol_name_bytes:
        # Om byte-värdet representerar en utskriftsbar karaktär omvandlas det till en bokstav
        if byte > 9:
            protocol_name_list.append(chr(byte))
        else:
            protocol_name_list.append(str(byte))
    protocol_name = "".join(protocol_name_list)
    decoded_packet["Protocol name"] = protocol_name
    current_byte += protocol_name_length_value + 1

    # Avkoda Connect flags (1 byte)
    if current_byte >= len(data):
        raise ValueError("Data saknas för att avkoda Connect flags.")
    connect_flags_byte = data[current_byte]
    connect_flags_bits = format(connect_flags_byte, "08b")
    decoded_packet["Username flag"] = (connect_flags_bits[0] == "1")
    decoded_packet["Password flag"] = (connect_flags_bits[1] == "1")
    decoded_packet["Retain flag"] = (connect_flags_bits[2] == "1")
    will_qos = connect_flags_bits[3] + connect_flags_bits[4]
    decoded_packet["Will QoS"] = int(will_qos, 2)
    decoded_packet["QoS 2 flag"] = (connect_flags_bits[4] == "1")
    decoded_packet["Will flag"] = (connect_flags_bits[5] == "1")
    decoded_packet["Clean Session flag"] = (connect_flags_bits[6] == "1")
    decoded_packet["Reserved flag"] = (connect_flags_bits[7] == "1")
    current_byte += 1

    # Avkoda Keep Alive (2 bytes)
    if current_byte + 1 >= len(data):
        raise ValueError("Data saknas för att avkoda Keep Alive.")
    keep_alive_bits = f"{data[current_byte]:08b}{data[current_byte + 1]:08b}"
    keep_alive_value = int(keep_alive_bits, 2)
    decoded_packet["Keep Alive"] = keep_alive_value
    current_byte += 2

    # Avkoda Payload length (2 bytes)
    if current_byte + 1 >= len(data):
        raise ValueError("Data saknas för att avkoda Payload length.")
    payload_length_bits = f"{data[current_byte]:08b}{data[current_byte + 1]:08b}"
    payload_length_value = int(payload_length_bits, 2)
    decoded_packet["Payload length"] = payload_length_value
    current_byte += 2

    # Avkoda Payload
    if current_byte + payload_length_value > len(data):
        raise ValueError("Data saknas för att avkoda Payload.")
    payload_bytes = data[current_byte: current_byte + payload_length_value]
    try:
        payload = payload_bytes.decode()
    except Exception as e:
        logging.error(f"Misslyckades att avkoda payload: {e}")
        payload = ""
    decoded_packet["Payload"] = payload

    return decoded_packet

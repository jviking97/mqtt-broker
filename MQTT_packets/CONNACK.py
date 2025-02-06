import logging
import MQTT_binary

# Konfigurera loggning (justera loggnivå vid behov)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def encode(session_present: bool = False, return_code: int = 0) -> bytes:
    # Hämta den binära representationen av CONNACK-pakettypen
    packet_type = MQTT_binary.get_bits("CONNACK")
    
    # Fasta flaggor
    flags = "0000"
    
    # Packet length är fast 2 bytes (för ack flagg och return code)
    packet_length = "00000010"
    
    # Connect acknowledge flags: 1 om session present, annars 0
    connect_acknowledge_flags = "00000001" if session_present else "00000000"
    
    # Bestäm connect return code och motsvarande text
    if return_code == 0:
        return_code_text = "Connection Accepted"
        connect_return_code = "00000000"
    elif return_code == 1:
        return_code_text = "Connection Refused, unacceptable protocol version"
        connect_return_code = "00000001"
    elif return_code == 2:
        return_code_text = "Connection Refused, identifier rejected"
        connect_return_code = "00000010"
    elif return_code == 3:
        return_code_text = "Connection Refused, Server unavailable"
        connect_return_code = "00000011"
    elif return_code == 4:
        return_code_text = "Connection Refused, bad user name or password"
        connect_return_code = "00000100"
    elif return_code == 5:
        return_code_text = "Connection Refused, not authorized"
        connect_return_code = "00000101"
    else:
        return_code_text = "Reserved for future use"
        connect_return_code = "11111111"
    
    # Skapa en avkodad representation för eventuell felsökning
    decoded_packet = {
        "Packet type": "CONNACK",
        "Flags": flags,
        "Session present": session_present,
        "Return code": return_code_text
    }
    logging.debug("Decoded packet: %s", decoded_packet)
    
    # Sätt ihop paketet genom att konkatenera de binära strängarna
    packet = (
        packet_type +
        flags +
        packet_length +
        connect_acknowledge_flags +
        connect_return_code
    )
    
    # Konvertera den binära strängen till bytes
    encoded_packet = int(packet, 2).to_bytes((len(packet) + 7) // 8, byteorder="big")
    return encoded_packet

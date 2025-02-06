import logging
import MQTT_binary

# Konfigurera logging med tidsstämpel, loggnivå och meddelande
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def encode(client_id: str) -> bytes:
    try:
        # Hämta den binära representationen av pakettypen
        packet_type = MQTT_binary.get_bits("PINGRESP")
    except Exception as e:
        logging.error(f"Could not fetch bits for PINGRESP: {e}")
        raise

    # Definiera fasta bitsträngar för flags och packet length
    flags = "0000"
    packet_length = "00000000"

    # Eventuellt: logga det "avkodade" paketet som en struktur (vid debug)
    decoded_packet = {
        "Packet type": "PINGRESP",
        "Flags": flags,
        "Packet length": packet_length
    }
    logging.debug(f"Decoded packet: {decoded_packet}")

    # Konstruera paketet genom att konkatenera de olika delarna
    packet_binary = packet_type + flags + packet_length

    # Logga att vi svarar på ping-requesten
    logging.info(f"Responded to ({client_id}) ping request.")

    # Konvertera den binära strängen till en bytes-array
    encoded_packet = int(packet_binary, 2).to_bytes((len(packet_binary) + 7) // 8, byteorder="big")
    return encoded_packet
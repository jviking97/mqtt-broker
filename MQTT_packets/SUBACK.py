import logging
import MQTT_binary

# Konfigurera loggning
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def encode(packet_identifier: int, return_codes: list[str]) -> bytes:
    # Hämta den binära representationen av SUBACK-pakettypen
    packet_type = MQTT_binary.get_bits('SUBACK')

    # Fasta flaggor för SUBACK
    flags = "0000"

    # Beräkna packet length: antal return codes plus 2 bytes för packet identifiern
    packet_length_value = len(return_codes) + 2
    packet_length = format(packet_length_value, "08b")

    # Konvertera packet identifier till en 16-bitars binär sträng
    packet_identifier_bits = format(packet_identifier, "016b")

    # Kombinera return codes till en enskild binär sträng
    return_codes_str = "".join(return_codes)

    # Sätt ihop hela paketet
    packet = packet_type + flags + packet_length + packet_identifier_bits + return_codes_str

    # Konvertera den binära strängen till bytes
    encoded_packet = int(packet, 2).to_bytes((len(packet) + 7) // 8, byteorder="big")
    logging.info("SUBACK encoded succesfully.")
    return encoded_packet

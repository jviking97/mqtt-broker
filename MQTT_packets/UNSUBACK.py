import logging
import MQTT_binary

# Konfigurera loggning (justera loggnivån vid behov)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def encode(packet_identifier: int) -> bytes:
    if not 0 <= packet_identifier <= 0xFFFF:
        raise ValueError("Packet identifier must be between 0 and 65535.")

    logging.info(f"Encoding UNSUBACK packet with packet identifier: {packet_identifier}")

    # Packet type: Hämta den binära representationen av UNSUBACK-pakettypen.
    packet_type = MQTT_binary.get_bits('UNSUBACK')

    # Flags: Fasta flaggbitar för UNSUBACK enligt specifikationen.
    flags = "0000"

    # Packet length: För UNSUBACK är längden fast, endast 2 byte (för packet identifier).
    packet_length = "00000010"

    # Packet identifier: Konvertera till en 16-bitars binär sträng.
    packet_identifier_bits = format(packet_identifier, "016b")

    # Sätt ihop hela paketet som en binär sträng.
    packet = packet_type + flags + packet_length + packet_identifier_bits

    # Konvertera den binära strängen till bytes.
    encoded_packet = int(packet, 2).to_bytes((len(packet) + 7) // 8, byteorder="big")
    return encoded_packet

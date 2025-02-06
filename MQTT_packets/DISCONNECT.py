import logging
import MQTT_database

# Konfigurera loggning
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

def handle(client_id: str) -> None:
    logging.info(f"Client ID ({client_id}) disconnected.")
import socket
import sys
import time
import logging
from threading import Thread, Lock
from MQTT_packets import packet_router, PUBLISH
import MQTT_decoder
import MQTT_database

HOST = "127.0.0.1"
PORT = 1883

# Konfigurera logging istället för print
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Broker:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connected_clients = {}  # Använd en dict istället för en lista: {client_id: client_socket}
        self.clients_lock = Lock()   # Skyddar åtkomst till connected_clients

    def start(self):
        MQTT_database.initialize_database()
        MQTT_database.topic_create('Temperature')
        MQTT_database.topic_create('Humidity')

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((self.host, self.port))
            logging.info(f"Binding to {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Bind failed: {e}")
            sys.exit(1)

        self.server_socket.listen(5)
        self.server_socket.settimeout(0.5)  # Gör att accept inte blockerar för evigt

        logging.info("Broker running and listening for active connections.")
        try:
            while True:
                try:
                    client_socket, address = self.server_socket.accept()
                    ip, port = address
                    logging.info(f"New connection from {ip}:{port}")
                    ClientHandler(client_socket, ip, port, self).start()
                except socket.timeout:
                    continue  # Går vidare för att kunna fånga KeyboardInterrupt
        except KeyboardInterrupt:
            logging.info("Exiting...")
        finally:
            self.server_socket.close()

    def add_client(self, client_id: str, client_socket: socket.socket):
        with self.clients_lock:
            self.connected_clients[client_id] = client_socket
            logging.info(f"Client {client_id} added.")

    def remove_client(self, client_id: str):
        with self.clients_lock:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                logging.info(f"Client {client_id} removed.")

    def send_to_all(self, packet: bytes):
        with self.clients_lock:
            for client_id, client_socket in list(self.connected_clients.items()):
                try:
                    client_socket.send(packet)
                except Exception as e:
                    logging.warning(f"Failed to send to {client_id}: {e}")
                    # Eventuellt ta bort klienten vid fel
                    self.remove_client(client_id)


class ClientHandler(Thread):
    def __init__(self, client_socket: socket.socket, ip: str, port: int, broker: Broker):
        super().__init__(daemon=True)  # Sätt tråden som daemon om du vill att den avslutas vid huvudprocessens slut
        self.client_socket = client_socket
        self.ip = ip
        self.port = port
        self.broker = broker
        self.client_id = None

    def run(self):
        try:
            while True:
                data = self.client_socket.recv(1024)
                if not data:
                    logging.info(f"No data from {self.client_id or self.ip}, closing connection.")
                    break

                incoming_packet = MQTT_decoder.decode(data)
                packet_type = incoming_packet.get("Packet type")
                logging.debug(f"Incoming packet ({packet_type}): {incoming_packet}")

                if packet_type == "CONNECT":
                    self.client_id = incoming_packet.get("Payload")
                    self.broker.add_client(self.client_id, self.client_socket)

                if packet_type == "DISCONNECT":
                    self.broker.remove_client(self.client_id)
                    break  # Avsluta loopen

                # Skicka paket via router
                outgoing_packet = packet_router.route_packet(incoming_packet, self.client_id)

                if packet_type == "PUBLISH":
                    self.broker.send_to_all(outgoing_packet)
                else:
                    self.client_socket.send(outgoing_packet)

                # Skicka retained message till nya prenumeranter
                if packet_type == "SUBSCRIBE":
                    topics = incoming_packet.get('Topics', [])
                    if topics:
                        topic = next(iter(topics[0]))
                        if topic in MQTT_database.session_get_topic(self.client_id) and MQTT_database.topic_exists(topic):
                            value = MQTT_database.topic_get_value(topic)
                            retained_packet = PUBLISH.encode(topic, value)
                            self.client_socket.send(retained_packet)

        except Exception as e:
            logging.error(f"Error in client thread for {self.client_id or self.ip}: {e}")
        finally:
            self.client_socket.close()
            if self.client_id:
                self.broker.remove_client(self.client_id)
            logging.info(f"Client thread {self.client_id or self.ip} exiting.")


def main():
    broker = Broker(HOST, PORT)
    broker.start()


if __name__ == "__main__":
    main()

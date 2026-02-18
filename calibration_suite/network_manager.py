# network_manager.py
import json
from kafka import KafkaProducer
import config

class NetworkManager:
    def __init__(self):
        self.producer = None
        self._setup_producer()

    def _setup_producer(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print(f"Warning: Kafka non raggiungibile ({e}). I dati rimarranno locali.")

    def send_calibration_data(self, data_list):
        """Invia l'intero dataset a Kafka."""
        if not self.producer:
            print("Kafka producer non inizializzato.")
            return

        payload = {
            "evento": "fine_taratura",
            "timestamp_invio": 123456789, # Usa time.time()
            "dati": data_list
        }

        print(f"Invio {len(data_list)} record a Kafka...")
        self.producer.send(config.KAFKA_TOPIC, payload)
        self.producer.flush()
        print("Invio completato.")

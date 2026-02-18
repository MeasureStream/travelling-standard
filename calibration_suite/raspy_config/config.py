# config.py
import os

# --- Configurazione Seriale ---
SERIAL_PORT = '/dev/ttyAMA0'  # Solitamente su RPi 5 è ttyAMA0 o ttyS0
BAUD_RATE = 9600
TIMEOUT = 1

# --- Configurazione Pacchetti ---
PACKET_SIZE = 10  # Numero di byte per considerare un pacchetto completo

# --- Comandi (in bytes) ---
CMD_START = b'\x01\x00\xSTART'  # Esempio: Sostituisci con i tuoi comandi reali
CMD_STOP = b'\x02\x00\xSTOP'

# --- Configurazioni File ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'tarature')

# --- Configurazione Kafka ---
KAFKA_BOOTSTRAP_SERVERS = ['192.168.1.100:9092'] # IP del tuo server
KAFKA_TOPIC = 'taratura_topic'

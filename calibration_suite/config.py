# config.py
import os

# --- Configurazione Seriale per PC Linux (USB) ---
# Se usi un convertitore USB-Seriale, solitamente è /dev/ttyUSB0 o /dev/ttyACM0
# Puoi controllare aprendo il terminale e digitando: ls /dev/tty*
SERIAL_PORT = "/dev/ttyUSB0"
FLUKE_PORT = "/dev/ttyUSB1"
FLUKE_VID = 0x0403
FLUKE_PID = 0x6001
BAUD_RATE = 115200
TIMEOUT = 1

# --- Configurazione Pacchetti ---
PACKET_SIZE = 128

# --- Comandi (in bytes) ---
# Nota: Assicurati che questi byte siano quelli che il tuo slave si aspetta
# CMD_CONNECT = b'\x00\x40\x40'
CMD_CONNECT = b"\x00\x01\x01"
CMD_START_CALIB_NTC = b"\x01\xf1\x04\x00\x64\x80"  # acquisici NTC (4) a 100 Hz (0064) e invia pacchetti da 128 campioni (80)
CMD_STOP_CALIB = b"\x01\xf2\x00"

# --- Configurazioni File ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "tarature")

# --- Configurazione Kafka ---
# Se stai testando in locale e non hai ancora Kafka, puoi lasciare così
# o impostare 'localhost:9092' se hai Kafka sul PC stesso.
KAFKA_BOOTSTRAP_SERVERS = ["192.168.1.100:9092"]
KAFKA_TOPIC = "taratura_topic"

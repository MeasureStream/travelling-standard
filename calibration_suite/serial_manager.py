# serial_manager.py
import time

import serial

import calibration_suite.config as config


class SerialManager:
    def __init__(self):
        self.ser = None

    def connect(self):
        """Apre la connessione seriale."""
        try:
            self.ser = serial.Serial(
                config.SERIAL_PORT, config.BAUD_RATE, timeout=config.TIMEOUT
            )
            print(f"Seriale connessa su {config.SERIAL_PORT}")
        except Exception as e:
            print(f"Errore connessione seriale: {e}")

    def send_command(self, command_bytes):
        """Invia un comando byte."""
        if self.ser and self.ser.is_open:
            self.ser.write(command_bytes)
            print(f"Comando inviato: {command_bytes}")
        else:
            print("Errore: Seriale non connessa.")

    def read_packet(self, size):
        """Legge un numero specifico di byte."""
        if self.ser and self.ser.is_open:
            # Legge 'size' bytes. Restituisce bytes vuoti se timeout.
            return self.ser.read(size)
        return b""

    def close(self):
        if self.ser:
            self.ser.close()


if __name__ == "__main__":

    sm = SerialManager()
    sm.connect()
    # Esempio di invio comando
    sm.send_command(config.CMD_CONNECT)
    # Esempio di lettura pacchetto
    packet = sm.read_packet(4)  # Legge ACK

    print(f"ACK ricevuto: {packet}")

    sm.send_command(config.CMD_START_CALIB_NTC)

    # while(5 minuti):
    start_time = time.time()

    while time.time() - start_time < 300:  # 5 minuti = 300 secondi
        packet = sm.read_packet(128)  # Legge un pacchetto da 128*2 byte
        if packet:
            print(f"Pacchetto ricevuto: {len(packet)} byte")
            for i in range(0, len(packet), 2):
                sample = int.from_bytes(packet[i : i + 2], byteorder="big")
                print(sample)
        else:
            time.sleep(0.001)  # Piccola pausa per evitare busy waiting

    sm.send_command(config.CMD_STOP_CALIB)
    print("Taratura terminata.")
    sm.close()

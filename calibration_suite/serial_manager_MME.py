# serial_manager.py
import serial
import time
import config

class SerialManager:
    def __init__(self):
        self.ser = None

    def connect(self):
        """Apre la connessione seriale."""
        try:
            # Inizializziamo con Parità SPACE (default per i dati)
            self.ser = serial.Serial(
                config.SERIAL_PORT,
                config.BAUD_RATE,
                timeout=config.TIMEOUT,
                parity=serial.PARITY_SPACE, # Default: bit 9 = 0
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            print(f"Seriale connessa su {config.SERIAL_PORT}")
        except Exception as e:
            print(f"Errore connessione seriale: {e}")

    def send_command(self, command_bytes):
        """
        Invia un comando gestendo la modalità Multiprocessor (9-bit).
        Il primo byte è considerato l'INDIRIZZO (Wakeup).
        I byte successivi sono i DATI.
        """
        if self.ser and self.ser.is_open:
            if len(command_bytes) < 1:
                return

            # Separa indirizzo (1° byte) e payload (resto)
            address_byte = command_bytes[0:1] # Mantiene il tipo bytes
            payload_bytes = command_bytes[1:]

            try:
                # 1. Invia INDIRIZZO (Wakeup) -> Parità MARK (9° bit = 1)
                self.ser.parity = serial.PARITY_MARK
                self.ser.write(address_byte)
                
                # Piccola pausa opzionale per stabilità su alcuni convertitori USB
                # time.sleep(0.001) 

                # 2. Invia DATI (se presenti) -> Parità SPACE (9° bit = 0)
                if len(payload_bytes) > 0:
                    self.ser.parity = serial.PARITY_SPACE
                    self.ser.write(payload_bytes)

                print(f"Comando MP inviato: Addr={address_byte.hex()} Data={payload_bytes.hex()}")

            except Exception as e:
                print(f"Errore durante l'invio MP: {e}")
            finally:
                # È buona norma rimettere a SPACE o NONE per letture future standard
                self.ser.parity = serial.PARITY_SPACE

        else:
            print("Errore: Seriale non connessa.")

    def read_packet(self, size):
        """Legge un numero specifico di byte."""
        if self.ser and self.ser.is_open:
            # Assicurati che la parità sia corretta per ricevere (di solito SPACE o NONE lato PC va bene 
            # perché l'STM32 invia il 9° bit, ma il PC lo ignora o lo checka)
            # Se l'STM32 risponde con 9 bit, il PC potrebbe dare errore di parità se non configurato.
            # Per semplicità, qui ignoriamo il check mettendo NONE o SPACE.
            return self.ser.read(size) 
        return b''

    def close(self):
        if self.ser:
            self.ser.close()

if __name__ == "__main__":
    sm = SerialManager()
    sm.connect()
    
    # Esempio basato sul tuo config.CMD_CONNECT (b'\x0F\x01\x01')
    # 0x0F verrà inviato con 9° bit = 1 (Sveglia STM32 se l'addr è 0x0F)
    # 0x01, 0x01 verranno inviati con 9° bit = 0
    sm.send_command(config.CMD_CONNECT)  
    
    packet = sm.read_packet(3)
    print(f"Pacchetto ricevuto: {packet}")
    packet = sm.read_packet(5).decode('ASCII', errors='ignore')
    print(f"Pacchetto ricevuto: {packet}")
    sm.close()
# main.py
import time
import threading
import config
from serial_manager import SerialManager
from storage_manager import StorageManager
from network_manager import NetworkManager

# --- Istanze Globali ---
serial_mgr = SerialManager()
storage_mgr = StorageManager()
network_mgr = NetworkManager()

# Evento per fermare il loop di lettura
stop_event = threading.Event()

def reading_loop():
    """Funzione eseguita in un thread separato per leggere i dati."""
    buffer = b''
    
    print("--- Inizio acquisizione dati ---")
    while not stop_event.is_set():
        # Legge piccoli chunk o byte per byte
        chunk = serial_mgr.read_packet(128) 
        
        if chunk:
            buffer += chunk
            
            # Se abbiamo raggiunto la dimensione del pacchetto
            if len(buffer) >= config.PACKET_SIZE:
                packet = buffer[:config.PACKET_SIZE]
                storage_mgr.save_packet(packet)
                buffer = buffer[config.PACKET_SIZE:] # Tieni il resto
                print(f"Pacchetto salvato: {packet.hex()}")

def finish_calibration():
    """Funzione chiamata allo scadere del timer."""
    print("\n--- Timer Scaduto: Fine Taratura ---")
    
    # 1. Ferma il loop di lettura
    stop_event.set()
    
    # 2. Invia comando di stop
    serial_mgr.send_command(config.CMD_STOP_CALIB)
    
    # Attendi un attimo per sicurezza
    time.sleep(1)
    
    # 3. Leggi il CSV completato e invia a Kafka
    print("Elaborazione dati per invio remoto...")
    data = storage_mgr.read_session_data()
    network_mgr.send_calibration_data(data)
    
    # 4. Pulizia
    serial_mgr.close()
    print("Ciclo completato. Programma terminato.")

def start_calibration(duration_minutes):
    """Avvia il processo di taratura."""
    serial_mgr.connect()
    
    # Prepara il file CSV
    storage_mgr.start_new_session()
    

    # Esempio di invio comando
    serial_mgr.send_command(config.CMD_CONNECT)  

    # Lettura ACK
    packet = serial_mgr.read_packet(4)  # Legge ACK

    print(f"ACK ricevuto: {packet}")


    # Invia comando start
    serial_mgr.send_command(config.CMD_START_CALIB_NTC)
    
    # Avvia il thread di lettura dati (non bloccante)
    stop_event.clear()
    reader_thread = threading.Thread(target=reading_loop)
    reader_thread.start()
    
    # Avvia il Timer (non bloccante)
    duration_seconds = duration_minutes * 60
    print(f"Timer avviato per {duration_minutes} minuti ({duration_seconds} sec).")
    
    timer = threading.Timer(duration_seconds, finish_calibration)
    timer.start()

if __name__ == "__main__":
    try:
        # Esempio: Avvia una taratura di 2 minuti
        minuti = float(input("Inserisci durata taratura in minuti: "))
        start_calibration(minuti)
        
        # Mantiene il main vivo finché i thread lavorano
        # In un'app reale potresti avere un loop o un'interfaccia qui
    except KeyboardInterrupt:
        print("Interruzione manuale...")
        stop_event.set()
        serial_mgr.close()

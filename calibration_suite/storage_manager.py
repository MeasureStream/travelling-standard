# storage_manager.py
import csv
import os
import time
from datetime import datetime

import calibration_suite.config as config


class StorageManager:
    def __init__(self):
        self.current_filename = None
        self._ensure_folder_exists()

    def _ensure_folder_exists(self):
        if not os.path.exists(config.DATA_FOLDER):
            os.makedirs(config.DATA_FOLDER)

    def start_new_session(self):
        """Crea il nome del file basato sull'orario corrente."""
        timestamp_str = datetime.now().strftime("%d%m%Y_%H%M%S")
        filename = f"Taratura_{timestamp_str}.csv"
        self.current_filename = os.path.join(config.DATA_FOLDER, filename)

        # Inizializza il file con gli header
        with open(self.current_filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Valore_Raw_Hex"])

        print(f"Creato nuovo file: {self.current_filename}")
        return self.current_filename

    def save_packet(self, data_bytes):
        """Salva i dati nel file CSV corrente."""
        if not self.current_filename:
            return

        timestamp = datetime.now().isoformat()
        # Convertiamo i byte in una stringa esadecimale leggibile per il CSV
        # Modifica 'data_bytes.hex()' se vuoi salvare un numero intero/float decodificato
        value_to_save = data_bytes.hex()

        with open(self.current_filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, value_to_save])

    def read_session_data(self):
        """Legge il file appena creato e restituisce una lista di dizionari."""
        if not self.current_filename or not os.path.exists(self.current_filename):
            return []

        data = []
        with open(self.current_filename, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data

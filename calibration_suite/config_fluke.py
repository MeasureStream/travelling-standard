import csv
import datetime
import json
import os
import time

import serial


class Fluke9142:
    def __init__(self, port, baudrate=9600, timeout=3):
        self.port = port
        self.ser = None
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            print(f"[HW] Connesso a {self.port}")
        except serial.SerialException as e:
            print(f"[ERR] Impossibile aprire la porta {port}: {e}")
            raise

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[HW] Connessione chiusa.")

    def _send_command(self, cmd):
        """Invia comando con terminatore CR (Carriage Return)."""
        full_cmd = f"{cmd}\r"
        self.ser.write(full_cmd.encode("ascii"))
        time.sleep(0.1)

    def _query(self, cmd):
        """Invia comando e legge risposta fino a CR LF."""
        self._send_command(cmd)
        try:
            response = self.ser.read_until(b"\r\n")
            return response.decode("ascii").strip()
        except Exception as e:
            print(f"[ERR] Errore lettura: {e}")
            return None

    def set_temperatura(self, temp):
        # """Imposta Set Point [cite: 481]"""
        self._send_command(f"SOUR:SPO {temp}")

    def avvia_riscaldamento(self):
        # """Abilita output [cite: 247]"""
        self._send_command("OUTP:STAT 1")

    def stop_riscaldamento(self):
        # """Disabilita output [cite: 247]"""
        self._send_command("OUTP:STAT 0")

    def leggi_temperatura(self):
        # """Legge temp. controllo [cite: 471]"""
        resp = self._query("SOUR:SENS:DATA?")
        try:
            return float(resp)
        except (ValueError, TypeError):
            return None

    def check_stabilita_hardware(self):
        # """Interroga il flag interno di stabilità [cite: 510]"""
        resp = self._query("SOUR:STAB:TEST?")
        return resp == "1"


# --- LOGICA DI ALTO LIVELLO ---


def salva_campione_csv(filename, target_temp, temp, stable_hw, phase="DWELL"):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                now_str,
                target_temp,
                temp,
                "SI" if stable_hw else "NO",
                phase,
            ]
        )


def crea_file_json():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"./calibration_suite/tarature/TemperaturaCorrente_{timestamp}.jsonl"

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    return filename


def salva_campione_json(filename, target, temperatura, stable_hw, phase):
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "target": target,
        "temperature": temperatura,
        "stable_hw": stable_hw,
        "phase": phase,
    }

    with open(filename, "a") as f:
        f.write(json.dumps(record) + "\n")


def crea_file_csv():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"./calibration_suite/tarature/TemperaturaCorrente_{timestamp}.csv"
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Timestamp", "Target (°C)", "Lettura (°C)", "Stabile_HW", "Fase"]
        )
    return filename


def attendi_stabilizzazione_robusta(
    pozzetto, target, tolleranza_approach=0.5, hold_seconds=10, initial_wait=30
):
    """
    Gestisce l'attesa intelligente della stabilità.

    Parametri:
    - target: Temperatura obiettivo
    - tolleranza_approach: Finestra entro la quale iniziare a controllare la stabilità (es. +/- 0.5°C)
    - hold_seconds: Per quanti secondi deve rimanere stabile prima di confermare
    - initial_wait: Tempo morto iniziale per permettere al sistema di muoversi (inerzia)
    """

    print(f"   -> [1/4] Attesa inerziale iniziale ({initial_wait} sec)...")
    time.sleep(initial_wait)

    start_stable_time = None

    while True:
        curr_temp = pozzetto.leggi_temperatura()
        if curr_temp is None:
            continue  # Gestione errori lettura

        # 1. Verifica Prossimità (Siamo vicini al target?)
        delta = abs(curr_temp - target)
        is_near = delta <= tolleranza_approach

        # 2. Verifica Stabilità Hardware (Il Fluke dice che è fermo?)
        is_hw_stable = pozzetto.check_stabilita_hardware()

        status_msg = ""

        if not is_near:
            # Caso A: Siamo ancora lontani (es. Target 35, Lettura 40)
            status_msg = f"In avvicinamento (Delta: {delta:.2f}°C)"
            start_stable_time = None  # Reset timer

        elif not is_hw_stable:
            # Caso B: Vicini ma instabili (oscillazione)
            status_msg = "Vicino ma INSTABILE (HW)"
            start_stable_time = None  # Reset timer

        else:
            # Caso C: Vicini E Stabili (HW dice OK) -> Contiamo il tempo
            if start_stable_time is None:
                start_stable_time = time.time()

            elapsed_stable = time.time() - start_stable_time
            remaining = hold_seconds - elapsed_stable
            status_msg = f"CONFIRMING STABILITY... -{int(remaining)}s"

            if elapsed_stable >= hold_seconds:
                print(
                    f"\r   -> [OK] Target {target}°C Raggiunto e Confermato! (Temp: {curr_temp}°C)      "
                )
                return  # Esce dalla funzione, stabilizzazione completata

        print(f"\r   T:{target} | R:{curr_temp} | {status_msg}          ", end="")
        time.sleep(1)


def esegui_ciclo_termico(
    pozzetto,
    step_lista,
    intervallo_log_sec=2,
    on_step_start=None,
    on_dwell_start=None,
    on_dwell_end=None,
    on_step_end=None,
):
    """
    Esegue il ciclo termico.
    intervallo_log_sec: Ogni quanti secondi salvare una riga nel CSV.
    """
    CSV = False
    if CSV:
        filename = crea_file_csv()
    else:
        filename = crea_file_json()
    print(f"\n--- INIZIO CICLO --- File: {filename}")
    print(f"--- Frequenza di salvataggio CSV: Ogni {intervallo_log_sec} secondi ---\n")

    pozzetto.avvia_riscaldamento()

    for i, (target_temp, durata_minuti) in enumerate(step_lista):
        print(f"\n>>> STEP {i+1}: Target {target_temp}°C per {durata_minuti} min <<<")

        # 1. Setup e Attesa Stabilizzazione (Usa la funzione robusta definita prima)
        pozzetto.set_temperatura(target_temp)

        if on_step_start:
            on_step_start(target_temp, durata_minuti, i + 1, len(step_lista))

        attendi_stabilizzazione_robusta(
            pozzetto, target_temp
        )  # Usa i default o personalizza qui

        if on_dwell_start:
            on_dwell_start(target_temp, durata_minuti)

        # 2. Fase di Registrazione (Dwell)
        print(f"   -> [REC] Avvio registrazione per {durata_minuti} minuti...")

        start_time = time.time()
        end_time = start_time + (durata_minuti * 60)
        last_save_time = 0  # Per gestire la frequenza di salvataggio

        while time.time() < end_time:
            now_loop = time.time()

            # --- BLOCCO ACQUISIZIONE ---
            # Eseguiamo la lettura dallo strumento
            # [cite_start]Utilizza il comando SOUR:SENS:DATA? [cite: 471]
            temp = pozzetto.leggi_temperatura()
            stable_hw = pozzetto.check_stabilita_hardware()

            # --- LOGICA DI SALVATAGGIO (Frequenza Variabile) ---
            # Salviamo su file SOLO se è passato il tempo impostato
            campionamento_hz = 100  # 100 campioni al secondo
            sleep_time = 1.0 / campionamento_hz
            if (now_loop - last_save_time) >= intervallo_log_sec:
                if CSV:
                    salva_campione_csv(filename, target_temp, temp, stable_hw, "DWELL")
                else:
                    salva_campione_json(filename, target_temp, temp, stable_hw, "DWELL")

                last_save_time = now_loop
                saved_flag = "*"  # Indicatore visivo che abbiamo salvato
            else:
                saved_flag = " "

            # --- AGGIORNAMENTO DISPLAY (Sempre ogni secondo) ---
            # Questo ti permette di vedere il timer scorrere anche se registri ogni ora
            remaining = int(end_time - now_loop)
            print(
                f"\r   [REC] {remaining}s rimasti | Temp: {temp}°C {saved_flag}", end=""
            )

            # Piccolo sleep per non sovraccaricare la CPU, ma mantenere il display fluido
            time.sleep(sleep_time)

        if on_dwell_end:
            on_dwell_end(target_temp, durata_minuti, i + 1, len(step_lista))

        if on_step_end:
            on_step_end(target_temp, durata_minuti)
    print("\n\n--- CICLO TERMINATO ---")
    pozzetto.stop_riscaldamento()


if __name__ == "__main__":
    PORTA = "/dev/ttyUSB0"

    # Lista step: (Temperatura, Minuti di permanenza)
    # Esempio: 45 -> 35

    PERIODO_ACQ = 1
    CICLO_TEST = [
        (25.0, 5),  # Primo step
        (50.0, 5),  # Secondo step (discesa)
        (120.0, 5),  # Terzo step (salita)
    ]

    try:
        fluke = Fluke9142(PORTA)
        esegui_ciclo_termico(fluke, CICLO_TEST, intervallo_log_sec=PERIODO_ACQ)
    except Exception as e:
        print(f"\nERRORE: {e}")
    finally:
        if "fluke" in locals():
            fluke.close()

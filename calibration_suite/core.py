# core.py
import threading
import time

import calibration_suite.config as config
from calibration_suite.config_fluke import Fluke9142, esegui_ciclo_termico
from calibration_suite.serial_manager import SerialManager

##from .network_manager import NetworkManager
from .storage_manager import StorageManager


class CalibrationController:
    def __init__(self, fluke_port=None):
        self.serial_mgr = SerialManager()
        self.storage_mgr = StorageManager()
        ##self.network_mgr = NetworkManager()
        self.fluke = None
        if fluke_port:

            try:
                self.fluke = Fluke9142(fluke_port)
            except Exception as e:
                print(f"[WARN] Fluke non disponibile: {e}")
        self.stop_event = threading.Event()
        self.on_finished = None
        self.on_error = None
        self.on_progress = None
        self.on_step_finished = None
        self.on_stable = None

        self._fluke_done_event = threading.Event()
        self._fluke_dwell_event = threading.Event()

    def wait_fluke_ready(self, target_temp, timeout_sec=300, check_interval=1):
        """Blocca finché il Fluke non è vicino al target e stabile, max timeout"""
        start = time.time()
        print("[INFO] Attesa Fluke pronto...")
        while time.time() - start < timeout_sec:
            temp = self.fluke.leggi_temperatura()
            stable = self.fluke.check_stabilita_hardware()
            if temp is None:
                print("[WARN] Lettura Fluke fallita, retry...")
            else:
                print(f"[INFO] Fluke: {temp:.2f}°C | Stabile: {stable}")
                if stable and abs(temp - target_temp) < 0.5:  # tolleranza 0.5°C
                    print("[INFO] Fluke pronto!")
                    return True
            time.sleep(check_interval)
        print("[ERROR] Timeout: Fluke non pronto")
        return False

    def start_steps(self, fluke_steps, fluke_log_interval=2):

        if not self.fluke:
            print("[ERROR] Fluke non disponibile")
            return

        if not fluke_steps:
            print("[ERROR] Nessuno step fornito")
            return

        self._fluke_done_event.clear()

        threading.Thread(
            target=self._fluke_thread_func1,
            args=(fluke_steps, fluke_log_interval),
            daemon=True,
        ).start()

        print("[INFO] Ciclo Fluke avviato")

    def start(
        self, duration_minutes, target_temp=None, fluke_steps=None, fluke_log_interval=2
    ):

        if self.fluke and fluke_steps:

            self._fluke_done_event.clear()
            self._fluke_dwell_event.clear()

            threading.Thread(
                target=self._fluke_thread_func,
                args=(fluke_steps, fluke_log_interval),
                daemon=True,
            ).start()

            print("[INFO] Attesa stabilizzazione Fluke...")

            # BLOCCA fino al dwell
            self._fluke_dwell_event.wait()

            print("[INFO] Avvio acquisizione MCU sincronizzata con Fluke")

        elif fluke_steps:
            print("[WARN] Fluke steps forniti ma nessun Fluke collegato")
            return

        self.serial_mgr.connect()
        self.storage_mgr.start_new_session()
        self.serial_mgr.send_command(config.CMD_CONNECT)
        ack = self.serial_mgr.read_packet(4)
        print(f"ACK ricevuto: {ack}")
        self.serial_mgr.send_command(config.CMD_START_CALIB_NTC)

        self.stop_event.clear()
        threading.Thread(target=self._reading_loop, daemon=True).start()

        threading.Thread(
            target=self._progress_loop, args=(duration_minutes,), daemon=True
        ).start()

        duration_seconds = duration_minutes * 60
        threading.Timer(duration_seconds, self.finish).start()
        print(f"Taratura avviata per {duration_minutes} minuti")

    def _reading_loop(self):
        buffer = b""
        while not self.stop_event.is_set():
            chunk = self.serial_mgr.read_packet(128)
            if chunk:
                buffer += chunk
                if len(buffer) >= config.PACKET_SIZE:
                    packet = buffer[: config.PACKET_SIZE]
                    self.storage_mgr.save_packet(packet)
                    buffer = buffer[config.PACKET_SIZE :]
                    print(f"Pacchetto salvato: {packet.hex()}")

    def _progress_loop(self, duration_minutes):
        duration_seconds = duration_minutes * 60
        start_time = time.time()
        while not self.stop_event.is_set():
            elapsed = time.time() - start_time
            percent = round((elapsed / duration_seconds) * 100)
            percent = min(percent, 100)

            if self.on_progress:
                self.on_progress(percent)
            time.sleep(0.5)

    def finish(self):
        print("--- Taratura terminata ---")
        self.stop_event.set()
        self.serial_mgr.send_command(config.CMD_STOP_CALIB)
        time.sleep(1)
        data = self.storage_mgr.read_session_data()
        print(f"data: {data}\n")
        ##self.network_mgr.send_calibration_data(data)
        self.serial_mgr.close()

        if self.on_finished:
            self.on_finished()

        print("Ciclo di taratura completato")

    def _fluke_thread_func(self, step_list, intervallo_log_sec=2):

        def dwell_callback(target_temp, durata):
            print("[INFO] Fluke in DWELL — avvio acquisizione MCU")
            self._fluke_dwell_event.set()

        try:

            esegui_ciclo_termico(
                self.fluke, step_list, intervallo_log_sec, on_dwell_start=dwell_callback
            )

        except Exception as e:

            print(f"[ERROR] Fluke thread: {e}")

            if self.on_error:
                self.on_error(str(e))

        finally:

            self._fluke_done_event.set()

    def _fluke_thread_func1(self, step_list, intervallo_log_sec=2):

        def on_step_start(target, durata, step, num_steps):
            if self.on_stable:
                self.on_stable(target, durata)

        def on_dwell_start(target, duration_minutes):

            print(f"[INFO] START acquisizione MCU @ {target}°C")

            self.serial_mgr.connect()

            self.storage_mgr.start_new_session()

            self.serial_mgr.send_command(config.CMD_CONNECT)
            ack = self.serial_mgr.read_packet(4)

            print(f"[INFO] ACK: {ack}")

            self.serial_mgr.send_command(config.CMD_START_CALIB_NTC)

            self.stop_event.clear()

            threading.Thread(target=self._reading_loop, daemon=True).start()
            threading.Thread(
                target=self._progress_loop, args=(duration_minutes,), daemon=True
            ).start()

            # duration_seconds = duration_minutes * 60
            # threading.Timer(duration_seconds, self.finish).start()
            print(f"Taratura avviata per {duration_minutes} minuti")

        def on_dwell_end(target, durata, step, num_steps):

            print(f"[INFO] STOP acquisizione MCU @ {target}°C")

            self.stop_event.set()

            self.serial_mgr.send_command(config.CMD_STOP_CALIB)

            time.sleep(1)

            data = self.storage_mgr.read_session_data()

            print(f"[INFO] Salvati {len(data)} campioni")

            if self.on_step_finished:
                self.on_step_finished(target, data, step, num_steps)

        try:

            esegui_ciclo_termico(
                self.fluke,
                step_list,
                intervallo_log_sec,
                on_step_start=on_step_start,
                on_dwell_start=on_dwell_start,
                on_dwell_end=on_dwell_end,
            )

        except Exception as e:

            print(f"[ERROR] Fluke thread: {e}")

            if self.on_error:
                self.on_error(str(e))

        finally:

            print("[INFO] Ciclo Fluke completato")

            self.finish()
            self._fluke_done_event.set()

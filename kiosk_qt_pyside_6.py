#!/usr/bin/env python3
"""
Kiosk-style Qt application (PySide6) for Raspberry Pi
- Fullscreen, single-window "kiosk" UI
- Main menu with large buttons (like the sketch)
- Placeholder logo drawn from embedded SVG
- Structure prepared for future cloud/service calls

Run: python3 kiosk_qt_pyside6.py
Dependencies: PySide6
Install: pip3 install PySide6

This is a single-file example intended as a starting point. Replace the
ServiceClient.fetch_* implementations with real network calls later.
"""
import sys
import textwrap
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QHBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
)

DEBUG = True

# ------------------------
# Simple service client stub
# ------------------------
class ServiceClient(QObject):
    """Placeholder client for future server interactions.

    Replace the methods with actual network code (requests, aiohttp, etc.).
    Keep network access off the GUI thread (use QThread or asyncio).
    """

    # Example signal to notify UI about new options
    options_updated = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        # configuration (e.g. base URL) can be injected here
        self.base_url = "https://example.com/api"

    def fetch_options(self):
        """Synchronously fetch available options.

        Currently a stub: emits a simulated list after a short delay.
        In production, do network IO on a worker thread and emit options_updated.
        """
        # Simulate network delay using QTimer singleShot (non-blocking)
        QTimer.singleShot(600, lambda: self.options_updated.emit([
            {"id": "thermal", "title": "Taratura Termica"},
            {"id": "fw", "title": "FW Update"},
            {"id": "status", "title": "Dev. Status"},
        ]))

    # Example of how a real fetch might look (commented):
    # def fetch_options_from_server(self):
    #     import requests
    #     resp = requests.get(f"{self.base_url}/options")
    #     resp.raise_for_status()
    #     data = resp.json()
    #     self.options_updated.emit(data)


# ------------------------
# Embedded Raspberry-like SVG as pixmap
# ------------------------
def raspberry_pixmap(size=80):
    """Return QPixmap painted from a small embedded SVG-like drawing.

    This avoids external image file dependencies. You can replace this
    function to load an external PNG/SVG if you prefer.
    """
    path = "./assets/pi-logo50x70.png"
    pix =  QPixmap(path)
    if not pix.isNull():
        return pix
    w = size
    h = size
    pix = QPixmap(w, h)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # draw a simple stylized raspberry: three circles + leaves
    p.setBrush(Qt.red)
    p.setPen(Qt.red)
    r = w * 0.18
    centers = [
        (w * 0.3, h * 0.45),
        (w * 0.5, h * 0.35),
        (w * 0.7, h * 0.45),
        (w * 0.4, h * 0.6),
        (w * 0.6, h * 0.6),
    ]
    for cx, cy in centers:
        p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))

    # leaves
    p.setBrush(Qt.darkGreen)
    p.setPen(Qt.darkGreen)
    p.drawEllipse(int(w * 0.45), int(h * 0.05), int(w * 0.2), int(h * 0.13))
    p.drawEllipse(int(w * 0.58), int(h * 0.02), int(w * 0.18), int(h * 0.12))

    p.end()
    return pix


# ------------------------
# Main UI
# ------------------------
class KioskWindow(QWidget):
    def __init__(self, service_client: ServiceClient):
        super().__init__()
        self.service_client = service_client

        self.setFixedSize(800, 480)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Nasconde il cursore direttamente
        if(DEBUG == False):
            self.setCursor(Qt.BlankCursor)

        self.init_ui()
        # connect service signals
        self.service_client.options_updated.connect(self.on_options)

        # ask client to populate options (non-blocking)
        self.service_client.fetch_options()

    def init_ui(self):
        # global layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 36, 36, 36)
        main_layout.setSpacing(20)

        # header
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_label.setPixmap(raspberry_pixmap(96))
        logo_label.setFixedSize(96, 96)

        title = QLabel("TRAVELLING MS QOL AO.1")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        header.addWidget(logo_label)
        header.addItem(QSpacerItem(12, 12, QSizePolicy.Expanding, QSizePolicy.Minimum))
        header.addWidget(title)
        header.addItem(QSpacerItem(12, 12, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addLayout(header)

        # central stacked widget
        self.stack = QStackedWidget()
        self.stack.setObjectName("stacked")

        self.main_page = QWidget()
        self.main_page.setObjectName("mainPage")
        self.main_page.setLayout(self.build_main_menu())

        self.stack.addWidget(self.main_page)

        # placeholder pages (created on demand)
        self.page_cache = {}

        main_layout.addWidget(self.stack, stretch=1)

        # footer (small help text)
        #footer = QLabel("Tocca una voce per procedere — usa il pulsante Indietro per tornare")
        #footer.setAlignment(Qt.AlignCenter)
        #footer.setObjectName("footer")
        #main_layout.addWidget(footer)

        # footer (small help text + quit button)
        #footer_layout = QHBoxLayout()
        #footer = QLabel("Tocca una voce per procedere — usa 'Quit' per uscire in sviluppo")
        #footer.setAlignment(Qt.AlignCenter)
        #footer.setObjectName("footer")

        #quit_btn = QPushButton("Quit")
        #quit_btn.setFixedHeight(40)
        #quit_btn.setFixedWidth(100)
        #quit_btn.clicked.connect(QApplication.instance().quit)

        #footer_layout.addWidget(footer)
        #footer_layout.addStretch(1)
        #footer_layout.addWidget(quit_btn)
        #main_layout.addLayout(footer_layout)


        # apply style
        self.apply_style()

    def build_main_menu(self):
        layout = QVBoxLayout()
        layout.setSpacing(28)

        # initially we show placeholder buttons; real options arrive from service
        self.option_buttons = []

        # create 3 big placeholders to match sketch
        for i in range(3):
            btn = QPushButton(f"Opzione {i+1}")
            btn.setFixedHeight(60)
            btn.setObjectName("menuButton")
            btn.clicked.connect(self.on_option_clicked)
            layout.addWidget(btn)
            self.option_buttons.append(btn)

        # spacer to center vertically
        layout.addStretch(1)
        return layout

    def apply_style(self):
        style = textwrap.dedent("""
        QWidget {
            background: #ffffff;
            color: #0b3d91;
            font-family: Arial, Helvetica, sans-serif;
        }
        #titleLabel {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 2px;
        }
        #stacked { padding: 12px; }
        #menuButton {
            border: 4px solid #1180ff;
            border-radius: 8px;
            font-size: 22px;
            font-weight: 600;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f3fbff);
        }
        #menuButton:pressed { background: #e6f2ff; }
        #footer { color: #3b6fb1; font-size: 12px; }
        """)
        self.setStyleSheet(style)

    def on_options(self, options):
        """Populate main menu buttons from options list.

        options: list of dicts {'id':..., 'title':...}
        """
        # ensure we have enough buttons; add if necessary
        needed = len(options)
        current = len(self.option_buttons)
        parent_layout = self.main_page.layout()
        if needed > current:
            for _ in range(needed - current):
                btn = QPushButton("Opzione aggiuntiva")
                btn.setFixedHeight(96)
                btn.setObjectName("menuButton")
                btn.clicked.connect(self.on_option_clicked)
                parent_layout.insertWidget(parent_layout.count() - 1, btn)
                self.option_buttons.append(btn)

        # update titles and attach id
        for btn, opt in zip(self.option_buttons, options):
            btn.setText(opt.get("title", ""))
            btn.setProperty("option_id", opt.get("id"))

    def on_option_clicked(self):
        sender = self.sender()
        option_id = sender.property("option_id") or sender.text()
        # create or show the page for this option
        page = self.page_cache.get(option_id)
        if page is None:
            page = self.build_option_page(option_id, sender.text())
            self.page_cache[option_id] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def build_option_page(self, option_id, title_text):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(16)

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:700;")
        v.addWidget(title)

        # content area: replace with real controls per option
        info = QLabel(f"Qui puoi configurare: {option_id}")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        v.addWidget(info, stretch=1)

        # example action button
        action = QPushButton("Esegui azione")
        action.setFixedHeight(64)
        action.clicked.connect(lambda: QMessageBox.information(self, "Azione", f"Azione per {option_id} eseguita"))
        v.addWidget(action)

        # back button
        back = QPushButton("Indietro")
        back.setFixedHeight(56)
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_page))
        v.addWidget(back)

        return w


# ------------------------
# Application entrypoint
# ------------------------
def main():
    app = QApplication(sys.argv)

    # create service client instance
    client = ServiceClient()

    # window
    win = KioskWindow(client)
    win.showFullScreen()

    # optional: Esc to quit during development (remove for final kiosk)
    def on_key(evt):
        if evt.key() == Qt.Key_Escape:
            app.quit()
    app.installEventFilter(win)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()


from serial.tools import list_ports

for p in list_ports.comports():
    print(f"Device: {p.device}")  # es: /dev/ttyUSB0
    print(f"Description: {p.description}")  # es: "USB Serial Device"
    print(f"VID:PID: {p.vid:#04x}:{p.pid:#04x}" if p.vid and p.pid else "VID:PID N/A")
    print(f"Serial Number: {p.serial_number}")
    print(f"Manufacturer: {p.manufacturer}")
    print(f"Product: {p.product}")
    print("-" * 40)

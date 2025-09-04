# mpv_embed_qt.py
import sys, json, socket, subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QWindow

SOCKET_PATH = "/tmp/mpvsocket"

def send_command(cmd):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.sendall((json.dumps(cmd) + "\n").encode("utf-8"))
            resp = client.recv(1024).decode("utf-8").strip()
            return resp
    except Exception as e:
        print("IPC error:", e)
        return None

class MpvWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NativeWindow)   # we need a native handle
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)

    def start_mpv(self):
        wid = int(self.winId())  # get native window id
        subprocess.Popen([
            "mpv",
            "--idle=yes",
            f"--wid={wid}",   # embed here
            f"--input-ipc-server={SOCKET_PATH}",
            "--no-terminal",
        ])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Embedded mpv in Qt")

        self.mpv_widget = MpvWidget(self)
        btn_open = QPushButton("Open Video")

        layout = QVBoxLayout()
        layout.addWidget(self.mpv_widget)
        layout.addWidget(btn_open)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        btn_open.clicked.connect(self.open_file)

        # launch mpv inside the widget
        self.mpv_widget.start_mpv()

    def open_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open video")
        if f:
            send_command({"command": ["loadfile", f]})

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec())
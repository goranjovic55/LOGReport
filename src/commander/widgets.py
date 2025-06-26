from enum import Enum
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class ConnectionState(Enum):
    """Connection state for Commander connections."""

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3


class ConnectionBar(QWidget):
    """Reusable connection bar widget with connect/disconnect logic."""

    # True for connect, False for disconnect
    connection_requested = pyqtSignal(bool)

    def __init__(self, ip_address: str, port: int) -> None:
        super().__init__()
        self.layout = QHBoxLayout()
        self.ip_edit = QLineEdit(ip_address)
        self.port_edit = QLineEdit(str(port))
        self.ip_edit.setPlaceholderText("IP Address")
        self.port_edit.setPlaceholderText("Port")
        self.status_icon = QLabel("\u25CB")  # Default disconnected icon
        self.connect_btn = QPushButton("Connect")

        self.layout.addWidget(QLabel("IP:"))
        self.layout.addWidget(self.ip_edit)
        self.layout.addWidget(QLabel("Port:"))
        self.layout.addWidget(self.port_edit)
        self.layout.addWidget(self.status_icon)
        self.layout.addWidget(self.connect_btn)
        self.layout.addStretch()
        self.setLayout(self.layout)

        self.connect_btn.clicked.connect(self._on_connect_button_clicked)
        self.update_status(ConnectionState.DISCONNECTED)

    def get_address(self) -> tuple[str, str]:
        """Return IP address and port from the input widgets."""

        return self.ip_edit.text(), self.port_edit.text()

    def update_status(self, state: ConnectionState) -> None:
        icons = {
            ConnectionState.DISCONNECTED: "\u25CB",
            ConnectionState.CONNECTING: "\u25D1",
            ConnectionState.CONNECTED: "\u25CF",
            ConnectionState.ERROR: "\u2a2f",
        }
        colors = {
            ConnectionState.DISCONNECTED: "#888",
            ConnectionState.CONNECTING: "orange",
            ConnectionState.CONNECTED: "lime",
            ConnectionState.ERROR: "red",
        }
        self.status_icon.setText(icons[state])
        self.status_icon.setStyleSheet(
            f"font-size: 16pt; color: {colors[state]};"
        )
        if state == ConnectionState.CONNECTED:
            self.connect_btn.setText("Disconnect")
        else:
            self.connect_btn.setText("Connect")

    def _on_connect_button_clicked(self) -> None:
        if self.connect_btn.text() == "Connect":
            self.connection_requested.emit(True)
        else:
            self.connection_requested.emit(False)


__all__ = ["ConnectionState", "ConnectionBar"]

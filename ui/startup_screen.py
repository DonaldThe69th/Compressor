"""
startup_screen.py
-----------------
Lightweight initializing screen shown while the main window is warmed up.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StartupScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setObjectName("startupScreen")
        self.setFixedSize(460, 240)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        title = QLabel("Compressor")
        title.setObjectName("startupTitle")

        subtitle = QLabel("Initializing workspace")
        subtitle.setObjectName("startupSubtitle")

        self._status = QLabel("Preparing interface...")
        self._status.setObjectName("startupStatus")
        self._status.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self._status)
        layout.addStretch()

    def set_status(self, text: str):
        self._status.setText(text)

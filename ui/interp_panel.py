"""
interp_panel.py
---------------
UI panel for frame interpolation settings.
Currently exposes 2x mode via minterpolate.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel, QFormLayout, QGroupBox
from PyQt6.QtCore import pyqtSignal
from core.video_job import VideoJob, InterpolationMode
from core.interpolation import InterpolationEngine
from ui.widgets import ConsistentComboBox, apply_surface_shadow


class InterpPanel(QWidget):
    """
    Frame interpolation configuration panel.

    Signals:
        settings_changed(): Emitted when user toggles or changes settings.
    """

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = InterpolationEngine()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 6, 4, 10)
        root.setSpacing(0)

        box = QGroupBox("Frame Interpolation")
        apply_surface_shadow(box, blur=24.0, offset_y=5.0)
        root.addWidget(box)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 18, 14, 14)

        # Enable toggle
        self._enable_check = QCheckBox("Enable Frame Interpolation")
        self._enable_check.stateChanged.connect(self._on_toggle)
        layout.addWidget(self._enable_check)

        # Options (disabled until checked)
        self._options_widget = QWidget()
        self._options_widget.setEnabled(False)
        form = QFormLayout(self._options_widget)

        self._mode_combo = ConsistentComboBox()
        self._mode_combo.addItem("2× (double frame rate)", InterpolationMode.TWO_X)
        self._mode_combo.currentIndexChanged.connect(self.settings_changed)
        form.addRow("Mode:", self._mode_combo)

        self._info_label = QLabel(
            "Uses FFmpeg minterpolate — motion-compensated interpolation.\n"
            "Note: this is CPU-intensive and will increase processing time."
        )
        self._info_label.setWordWrap(True)
        self._info_label.setObjectName("infoLabel")
        form.addRow(self._info_label)

        layout.addWidget(self._options_widget)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_toggle(self, state: int):
        enabled = bool(state)
        self._options_widget.setEnabled(enabled)
        self.settings_changed.emit()

    # ------------------------------------------------------------------
    # Apply / read
    # ------------------------------------------------------------------

    def apply_to_job(self, job: VideoJob):
        """Configure interpolation on the job based on current UI state."""
        if self._enable_check.isChecked():
            mode = self._mode_combo.currentData()
            if mode == InterpolationMode.TWO_X:
                self._engine.apply_2x(job)
        else:
            self._engine.disable(job)

    def populate_from_job(self, job: VideoJob):
        is_active = job.interpolation_mode != InterpolationMode.NONE
        self._enable_check.setChecked(is_active)
        self._options_widget.setEnabled(is_active)

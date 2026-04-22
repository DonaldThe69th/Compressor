"""
upscale_panel.py
----------------
UI panel for video upscaling settings.
"""


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox,
    QFormLayout, QLabel, QSpinBox, QHBoxLayout
)
from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtCore import pyqtSignal
from core.video_job import VideoJob, UpscaleMode
from core.upscaling import UpscalingEngine, UPSCALE_PRESETS
from ui.widgets import ConsistentComboBox, apply_surface_shadow


class UpscalePanel(QWidget):
    """
    Upscaling configuration panel.

    Signals:
        settings_changed(): Emitted when user changes any setting.
    """

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._engine = UpscalingEngine()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 6, 4, 10)
        root.setSpacing(0)

        box = QGroupBox("Upscaling")
        apply_surface_shadow(box, blur=24.0, offset_y=5.0)
        root.addWidget(box)

        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 18, 14, 14)

        # Enable toggle
        self._enable_check = QCheckBox("Enable Upscaling")
        self._enable_check.stateChanged.connect(self._on_toggle)
        layout.addWidget(self._enable_check)

        # Options
        self._options_widget = QWidget()
        self._options_widget.setEnabled(False)
        form = QFormLayout(self._options_widget)

        # Method
        self._method_combo = ConsistentComboBox()
        self._method_combo.addItem("Lanczos (FFmpeg built-in)", UpscaleMode.LANCZOS)
        self._method_combo.addItem("Real-ESRGAN (AI) — coming soon", None)
        self._method_combo.currentIndexChanged.connect(self._on_method_changed)
        form.addRow("Method:", self._method_combo)

        # Preset or custom
        self._preset_combo = ConsistentComboBox()
        self._preset_combo.addItem("Custom", None)
        for name in UPSCALE_PRESETS:
            self._preset_combo.addItem(name, name)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form.addRow("Target Resolution:", self._preset_combo)

        # Custom resolution
        self._custom_w = QSpinBox()
        self._custom_w.setRange(1, 7680)
        self._custom_w.setValue(1920)
        self._custom_h = QSpinBox()
        self._custom_h.setRange(1, 4320)
        self._custom_h.setValue(1080)
        custom_row = QWidget()
        cr_layout = QHBoxLayout(custom_row)
        cr_layout.setContentsMargins(0, 0, 0, 0)
        cr_layout.addWidget(self._custom_w)
        cr_layout.addWidget(QLabel("×"))
        cr_layout.addWidget(self._custom_h)
        self._custom_widget = custom_row
        form.addRow("Custom (W×H):", self._custom_widget)

        # Info
        self._info_label = QLabel("")
        self._info_label.setWordWrap(True)
        self._info_label.setObjectName("infoLabel")
        form.addRow(self._info_label)

        layout.addWidget(self._options_widget)
        layout.addStretch()

        self._update_info()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_toggle(self, state: int):
        self._options_widget.setEnabled(bool(state))
        self.settings_changed.emit()

    def _on_method_changed(self):
        data = self._method_combo.currentData()
        if data is None:
            # Real-ESRGAN selected but not available
            if not UpscalingEngine.is_realesrgan_available():
                self._info_label.setText(
                    "⚠ Real-ESRGAN is not installed. "
                    "Install 'realesrgan-ncnn-vulkan' and add it to your PATH."
                )
        else:
            self._info_label.setText("")
        self.settings_changed.emit()

    def _on_preset_changed(self):
        is_custom = self._preset_combo.currentData() is None
        self._custom_widget.setVisible(is_custom)
        self.settings_changed.emit()

    def _update_info(self):
        self._custom_widget.setVisible(True)   # default to custom visible

    # ------------------------------------------------------------------
    # Apply / read
    # ------------------------------------------------------------------

    def apply_to_job(self, job: VideoJob):
        if not self._enable_check.isChecked():
            self._engine.disable(job)
            return

        preset = self._preset_combo.currentData()
        if preset:
            self._engine.apply_preset(job, preset)
        else:
            self._engine.apply_lanczos(job, self._custom_w.value(), self._custom_h.value())

    def populate_from_job(self, job: VideoJob):
        active = job.upscale_mode != UpscaleMode.NONE
        self._enable_check.setChecked(active)
        self._options_widget.setEnabled(active)
        if job.upscale_width:
            self._custom_w.setValue(job.upscale_width)
        if job.upscale_height:
            self._custom_h.setValue(job.upscale_height)

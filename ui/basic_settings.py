"""
basic_settings.py
-----------------
Settings tab: global compression default + output options.
The global default pre-fills each new job row but can be overridden per-row.
"""

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QPushButton, QHBoxLayout, QLabel,
    QButtonGroup, QRadioButton, QGroupBox, QVBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from core.video_job import VideoJob, SizeMode


COMMON_RESOLUTIONS = [
    "Original", "3840x2160 (4K)", "2560x1440 (1440p)",
    "1920x1080 (1080p)", "1280x720 (720p)", "854x480 (480p)", "Custom"
]
OUTPUT_FORMATS = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv"]
FPS_ORIGINAL   = 0.0


class BasicSettingsPanel(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(14)
        root.addWidget(self._make_default_group())
        root.addWidget(self._make_output_group())
        root.addStretch()

    # ------------------------------------------------------------------
    # Default compression group
    # ------------------------------------------------------------------

    def _make_default_group(self) -> QGroupBox:
        box = QGroupBox("Default Compression (applied to each new file)")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        note = QLabel(
            "This sets the starting value for every file you add.\n"
            "You can override it per-file directly in the queue."
        )
        note.setObjectName("metaLabel")
        note.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(note)

        # Mode radio
        mode_row = QHBoxLayout()
        self._pct_radio = QRadioButton("Percentage reduction")
        self._mb_radio  = QRadioButton("Target size (MB)")
        self._pct_radio.setChecked(True)
        self._mode_group = QButtonGroup()
        self._mode_group.addButton(self._pct_radio, 0)
        self._mode_group.addButton(self._mb_radio,  1)
        self._mode_group.buttonClicked.connect(self._on_mode_changed)
        mode_row.addWidget(self._pct_radio)
        mode_row.addWidget(self._mb_radio)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Value row
        value_row = QHBoxLayout()

        self._pct_spin = QDoubleSpinBox()
        self._pct_spin.setRange(1.0, 99.0)
        self._pct_spin.setValue(50.0)
        self._pct_spin.setSuffix(" % smaller")
        self._pct_spin.setDecimals(0)
        self._pct_spin.setFixedWidth(130)
        self._pct_spin.setToolTip(
            "Each new file will default to this percentage reduction.\n"
            "50% = output is half the original size."
        )
        self._pct_spin.valueChanged.connect(self.settings_changed)

        self._mb_spin = QDoubleSpinBox()
        self._mb_spin.setRange(0.1, 100_000.0)
        self._mb_spin.setValue(20.0)
        self._mb_spin.setSuffix(" MB")
        self._mb_spin.setDecimals(1)
        self._mb_spin.setFixedWidth(130)
        self._mb_spin.setToolTip("Each new file will default to this target size.")
        self._mb_spin.setVisible(False)
        self._mb_spin.valueChanged.connect(self.settings_changed)

        value_row.addWidget(self._pct_spin)
        value_row.addWidget(self._mb_spin)
        value_row.addStretch()
        layout.addLayout(value_row)

        return box

    # ------------------------------------------------------------------
    # Output group
    # ------------------------------------------------------------------

    def _make_output_group(self) -> QGroupBox:
        box = QGroupBox("Output")
        form = QFormLayout(box)
        form.setSpacing(8)

        self._format_combo = QComboBox()
        self._format_combo.addItems(OUTPUT_FORMATS)
        self._format_combo.setToolTip("Output container format")
        self._format_combo.currentIndexChanged.connect(self.settings_changed)
        form.addRow("Format:", self._format_combo)

        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(COMMON_RESOLUTIONS)
        self._resolution_combo.setToolTip("Output resolution")
        self._resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        form.addRow("Resolution:", self._resolution_combo)

        custom_row = QWidget()
        cl = QHBoxLayout(custom_row)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(6)
        self._custom_w = QSpinBox()
        self._custom_w.setRange(2, 7680)
        self._custom_w.setValue(1920)
        self._custom_w.setSuffix(" px")
        self._custom_h = QSpinBox()
        self._custom_h.setRange(2, 4320)
        self._custom_h.setValue(1080)
        self._custom_h.setSuffix(" px")
        cl.addWidget(self._custom_w)
        cl.addWidget(QLabel("×"))
        cl.addWidget(self._custom_h)
        cl.addStretch()
        self._custom_res_widget = custom_row
        self._custom_res_widget.setVisible(False)
        form.addRow("Custom (W×H):", self._custom_res_widget)

        self._fps_spin = QDoubleSpinBox()
        self._fps_spin.setRange(FPS_ORIGINAL, 240.0)
        self._fps_spin.setValue(FPS_ORIGINAL)
        self._fps_spin.setSingleStep(1.0)
        self._fps_spin.setDecimals(3)
        self._fps_spin.setSuffix(" fps")
        self._fps_spin.setSpecialValueText("Original")
        self._fps_spin.setToolTip("Leave at Original to keep source frame rate.")
        self._fps_spin.valueChanged.connect(self.settings_changed)
        form.addRow("Frame Rate:", self._fps_spin)

        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Same folder as source")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_output)
        path_row = QWidget()
        pl = QHBoxLayout(path_row)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)
        pl.addWidget(self._output_edit)
        pl.addWidget(browse_btn)
        form.addRow("Output Folder:", path_row)

        return box

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_mode_changed(self):
        is_pct = self._pct_radio.isChecked()
        self._pct_spin.setVisible(is_pct)
        self._mb_spin.setVisible(not is_pct)
        self.settings_changed.emit()

    def _on_resolution_changed(self):
        self._custom_res_widget.setVisible(
            self._resolution_combo.currentText() == "Custom"
        )
        self.settings_changed.emit()

    def _browse_output(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._output_edit.setText(folder)
            self.settings_changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_default_mode(self) -> SizeMode:
        return SizeMode.PERCENT if self._pct_radio.isChecked() else SizeMode.MB

    def get_default_value(self) -> float:
        if self._pct_radio.isChecked():
            return self._pct_spin.value()
        return self._mb_spin.value()

    def get_output_folder(self) -> str | None:
        t = self._output_edit.text().strip()
        return t if t else None

    def get_output_format(self) -> str:
        return self._format_combo.currentText()

    def apply_to_job(self, job: VideoJob):
        """Apply output settings (format, resolution, fps) to a job."""
        job.output_format = self._format_combo.currentText()

        res = self._resolution_combo.currentText()
        if res == "Custom":
            job.target_width  = self._custom_w.value()
            job.target_height = self._custom_h.value()
        elif res != "Original":
            try:
                dims = res.split(" ")[0].split("x")
                job.target_width  = int(dims[0])
                job.target_height = int(dims[1])
            except (IndexError, ValueError):
                pass

        fps = self._fps_spin.value()
        job.target_fps = fps if fps > FPS_ORIGINAL else None
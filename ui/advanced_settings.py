"""
advanced_settings.py
--------------------
Panel for advanced FFmpeg parameters: codec, CRF, bitrate, preset, audio.
"""

from PyQt6.QtWidgets import (
    QWidget, QFormLayout, QComboBox, QSlider,
    QSpinBox, QCheckBox, QLabel, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from core.video_job import VideoJob
from core.compression import SPEED_PRESETS, CRF_DEFAULTS
from utils.format_utils import CODEC_TO_FFMPEG, FFMPEG_TO_CODEC


VIDEO_CODECS = ["H.264", "H.265", "VP9", "AV1", "Copy"]
AUDIO_CODECS = ["copy", "aac", "mp3", "opus", "flac", "none"]

# Sentinel value meaning "let the worker decide based on source bitrate"
CRF_AUTO = -1


class AdvancedSettingsPanel(QWidget):
    """
    Exposes low-level FFmpeg controls.

    CRF slider has an "Auto" position (leftmost, value = CRF_AUTO sentinel)
    which tells the worker to compute a safe CRF from the source bitrate.
    Explicit values 0–51 override that.
    """

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Video codec ---
        self._codec_combo = QComboBox()
        self._codec_combo.addItems(VIDEO_CODECS)
        self._codec_combo.setToolTip(
            "Video codec for re-encoding.\n'copy' passes the stream through without re-encoding."
        )
        self._codec_combo.currentIndexChanged.connect(self._on_codec_changed)
        layout.addRow("Video Codec:", self._codec_combo)

        # --- CRF slider ---
        # Range: -1 (Auto) to 51. We shift the slider range to 0–52
        # where position 0 = Auto, positions 1–52 = CRF 0–51.
        crf_widget = QWidget()
        crf_layout = QHBoxLayout(crf_widget)
        crf_layout.setContentsMargins(0, 0, 0, 0)
        crf_layout.setSpacing(8)

        self._crf_slider = QSlider(Qt.Orientation.Horizontal)
        self._crf_slider.setRange(0, 52)      # 0=Auto, 1..52 → CRF 0..51
        self._crf_slider.setValue(0)           # default = Auto
        self._crf_slider.setToolTip(
            "CRF (Constant Rate Factor): lower = better quality, larger file.\n"
            "Auto = worker picks CRF based on source bitrate to avoid inflation."
        )
        self._crf_slider.valueChanged.connect(self._on_crf_changed)

        self._crf_label = QLabel("Auto")
        self._crf_label.setFixedWidth(36)

        crf_layout.addWidget(self._crf_slider)
        crf_layout.addWidget(self._crf_label)
        layout.addRow("CRF (quality):", crf_widget)

        # --- Encoding preset ---
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(SPEED_PRESETS)
        self._preset_combo.setCurrentText("medium")
        self._preset_combo.setToolTip(
            "Encoding speed vs compression tradeoff.\n"
            "'slow' produces smaller files; 'fast' encodes quicker."
        )
        self._preset_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addRow("Encoding Speed:", self._preset_combo)

        # --- Target bitrate ---
        self._bitrate_spin = QSpinBox()
        self._bitrate_spin.setRange(0, 100_000)
        self._bitrate_spin.setValue(0)
        self._bitrate_spin.setSuffix(" kbps")
        self._bitrate_spin.setSpecialValueText("Auto (use CRF)")
        self._bitrate_spin.setToolTip(
            "Force a specific output bitrate.\nLeave at 0 to use CRF mode instead."
        )
        self._bitrate_spin.valueChanged.connect(self.settings_changed)
        layout.addRow("Target Bitrate:", self._bitrate_spin)

        # --- Audio codec ---
        self._audio_combo = QComboBox()
        self._audio_combo.addItems(AUDIO_CODECS)
        self._audio_combo.setToolTip("'copy' passes audio through without re-encoding (fastest).")
        self._audio_combo.currentIndexChanged.connect(self.settings_changed)
        layout.addRow("Audio Codec:", self._audio_combo)

        # --- Strip audio ---
        self._strip_audio_check = QCheckBox("Strip audio (video only output)")
        self._strip_audio_check.stateChanged.connect(self.settings_changed)
        layout.addRow("", self._strip_audio_check)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_crf_changed(self, slider_val: int):
        if slider_val == 0:
            self._crf_label.setText("Auto")
        else:
            self._crf_label.setText(str(slider_val - 1))   # shift back to 0-51
        self.settings_changed.emit()

    def _on_codec_changed(self):
        self._crf_slider.setValue(0)
        self.settings_changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_to_job(self, job: VideoJob):
        """Write current panel values into a VideoJob."""
        display = self._codec_combo.currentText()
        ffmpeg_name = CODEC_TO_FFMPEG.get(display, display)
        job.video_codec = None if ffmpeg_name == "copy" else ffmpeg_name

        bitrate = self._bitrate_spin.value()
        if bitrate > 0:
            job.bitrate_kbps = bitrate
            job.crf = None          # bitrate mode — worker ignores CRF
        else:
            slider_val = self._crf_slider.value()
            if slider_val == 0:
                job.crf = None      # Auto — worker calls _safe_crf()
            else:
                job.crf = slider_val - 1    # shift back to 0–51
            job.bitrate_kbps = None

        job.preset = self._preset_combo.currentText()

        audio = self._audio_combo.currentText()
        job.strip_audio = (audio == "none")
        job.audio_codec = None if audio in ("none", "copy") else audio

    def populate_from_job(self, job: VideoJob):
        """Reverse-populate controls from an existing VideoJob."""
        if job.video_codec:
            display = FFMPEG_TO_CODEC.get(job.video_codec, job.video_codec)
            idx = self._codec_combo.findText(display)
            if idx >= 0:
                self._codec_combo.setCurrentIndex(idx)
        if job.crf is not None:
            self._crf_slider.setValue(job.crf + 1)   # shift to slider range
        else:
            self._crf_slider.setValue(0)             # Auto
        if job.bitrate_kbps:
            self._bitrate_spin.setValue(job.bitrate_kbps)
        if job.preset:
            self._preset_combo.setCurrentText(job.preset)
        self._strip_audio_check.setChecked(job.strip_audio)
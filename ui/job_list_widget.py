"""
job_list_widget.py
------------------
Queue of VideoJob rows. Each row has an inline compression target control
(% or MB) that pre-fills from the global default but can be overridden.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from core.video_job import VideoJob, JobStatus, SizeMode


STATUS_STYLE = {
    JobStatus.PENDING:   ("Pending",    "color: #999999;"),
    JobStatus.RUNNING:   ("Processing", "color: #3388cc;"),
    JobStatus.DONE:      ("Done",       "color: #339944;"),
    JobStatus.FAILED:    ("Failed",     "color: #cc4444;"),
    JobStatus.CANCELLED: ("Cancelled",  "color: #aa7700;"),
}


class JobRowWidget(QWidget):
    """
    Single job row.
    Left side:  filename + source metadata
    Right side: size mode combo + value spinner + status + remove button
    Bottom:     3px progress bar
    """

    remove_requested = pyqtSignal(object)

    def __init__(self, job: VideoJob,
                 default_mode: SizeMode = SizeMode.PERCENT,
                 default_value: float = 50.0,
                 parent=None):
        super().__init__(parent)
        self.job = job
        self.setObjectName("jobRow")
        self.setFixedHeight(62)
        self._build_ui(default_mode, default_value)
        # Write initial values into job
        self._sync_to_job()

    def _build_ui(self, default_mode: SizeMode, default_value: float):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 6, 12, 0)
        outer.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(10)

        # --- Left: filename + metadata ---
        info = QVBoxLayout()
        info.setSpacing(1)

        self._name_label = QLabel(self.job.display_name())
        self._name_label.setObjectName("jobName")
        self._name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        self._meta_label = QLabel(self._build_meta())
        self._meta_label.setObjectName("jobMeta")

        info.addWidget(self._name_label)
        info.addWidget(self._meta_label)
        top.addLayout(info)

        # --- Right: size control + status + remove ---
        # Mode selector: "%" or "MB"
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("%",  SizeMode.PERCENT)
        self._mode_combo.addItem("MB", SizeMode.MB)
        self._mode_combo.setFixedWidth(58)
        self._mode_combo.setFixedHeight(26)
        self._mode_combo.setCurrentIndex(
            0 if default_mode == SizeMode.PERCENT else 1
        )
        self._mode_combo.setToolTip("% = reduce by percentage  |  MB = target file size")
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        # Value input — plain QLineEdit, no floating frame
        self._value_input = QLineEdit()
        self._value_input.setObjectName("jobValueInput")
        self._value_input.setFixedWidth(80)
        self._value_input.setFixedHeight(26)
        self._value_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Only allow positive numbers with up to 1 decimal place
        validator = QRegularExpressionValidator(
            QRegularExpression(r"^\d{0,6}(\.\d{0,1})?$")
        )
        self._value_input.setValidator(validator)
        self._value_input.textChanged.connect(self._sync_to_job)
        self._apply_mode_range(default_mode, default_value)

        # Status label
        self._status_label = QLabel("Pending")
        self._status_label.setObjectName("jobMeta")
        self._status_label.setFixedWidth(68)
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._status_label.setStyleSheet("color: #999999; font-size: 11px;")

        # Remove button
        self._remove_btn = QPushButton("✕")
        self._remove_btn.setObjectName("removeButton")
        self._remove_btn.setFixedSize(22, 22)
        self._remove_btn.setToolTip("Remove from queue")
        self._remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(self.job)
        )

        top.addWidget(self._mode_combo)
        top.addWidget(self._value_input)
        top.addWidget(self._status_label)
        top.addWidget(self._remove_btn)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(3)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)

        outer.addLayout(top)
        outer.addWidget(self._progress_bar)
        outer.addWidget(line)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_meta(self) -> str:
        m = self.job.source_metadata
        if not m:
            return ""
        fps  = f"{m.fps:.3f}".rstrip("0").rstrip(".")
        mb   = m.file_size / (1024 * 1024) if m.file_size else 0
        return f"{m.width}×{m.height}  {fps} fps  {m.codec_name.upper()}  {mb:.1f} MB"

    def _apply_mode_range(self, mode: SizeMode, value: float):
        self._value_input.blockSignals(True)
        if mode == SizeMode.PERCENT:
            self._value_input.setPlaceholderText("1–99")
            self._value_input.setToolTip(
                "Reduce file size by this percentage.\n"
                "e.g. 50 → output is half the source size."
            )
        else:
            self._value_input.setPlaceholderText("MB")
            self._value_input.setToolTip("Target output file size in megabytes.")
        self._value_input.setText(str(int(value)) if value == int(value) else f"{value:.1f}")
        self._value_input.blockSignals(False)

    def _current_mode(self) -> SizeMode:
        return self._mode_combo.currentData()

    def _on_mode_changed(self):
        mode = self._current_mode()
        default = 50.0 if mode == SizeMode.PERCENT else 15.0
        self._apply_mode_range(mode, default)
        self._sync_to_job()

    def _sync_to_job(self):
        """Push current control values into the job."""
        self.job.size_mode = self._current_mode()
        try:
            self.job.size_value = float(self._value_input.text())
        except ValueError:
            pass  # keep previous value if input is incomplete

    # ------------------------------------------------------------------
    # Called by JobListWidget on queue events
    # ------------------------------------------------------------------

    def set_progress(self, pct: float):
        self._progress_bar.setValue(int(pct))

    def set_status(self, status: JobStatus):
        text, style = STATUS_STYLE.get(status, ("Unknown", ""))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"{style} font-size: 11px;")

        if status == JobStatus.DONE:
            self._progress_bar.setValue(100)
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #339944; }"
            )
        elif status == JobStatus.FAILED:
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #cc4444; }"
            )
        elif status == JobStatus.RUNNING:
            self._progress_bar.setStyleSheet("")

        # Lock controls while running
        is_running = (status == JobStatus.RUNNING)
        self._mode_combo.setEnabled(not is_running)
        self._value_input.setEnabled(not is_running)
        self._remove_btn.setEnabled(not is_running)


class JobListWidget(QWidget):
    """Scrollable list of JobRowWidgets with header and empty state."""

    job_remove_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: dict[str, JobRowWidget] = {}
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(26)
        header.setStyleSheet(
            "background-color: #f0f0f0; border-bottom: 1px solid #e0e0e0;"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 12, 0)

        queue_lbl = QLabel("Queue")
        queue_lbl.setObjectName("sectionLabel")

        self._count_label = QLabel("0 files")
        self._count_label.setObjectName("metaLabel")
        self._count_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        h_layout.addWidget(queue_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self._count_label)
        outer.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #ffffff;")

        self._container = QWidget()
        self._container.setStyleSheet("background-color: #ffffff;")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_layout.setSpacing(0)
        self._list_layout.setContentsMargins(0, 0, 0, 0)

        self._empty_label = QLabel(
            "No files added yet.\nDrop videos above or click to browse."
        )
        self._empty_label.setObjectName("metaLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #cccccc; padding: 24px;")
        self._list_layout.addWidget(self._empty_label)

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_job(self, job: VideoJob,
                default_mode: SizeMode = SizeMode.PERCENT,
                default_value: float = 50.0):
        """Add a job row pre-filled with the global default."""
        self._empty_label.setVisible(False)
        row = JobRowWidget(job,
                           default_mode=default_mode,
                           default_value=default_value)
        row.remove_requested.connect(self.job_remove_requested)
        self._rows[job.input_path] = row
        self._list_layout.addWidget(row)
        self._refresh_count()

    def update_progress(self, job: VideoJob, pct: float):
        if row := self._rows.get(job.input_path):
            row.set_progress(pct)

    def update_status(self, job: VideoJob):
        if row := self._rows.get(job.input_path):
            row.set_status(job.status)

    def remove_job(self, job: VideoJob):
        if row := self._rows.pop(job.input_path, None):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._refresh_count()

    def _refresh_count(self):
        n = len(self._rows)
        self._count_label.setText(f"{n} file{'s' if n != 1 else ''}")
        self._empty_label.setVisible(n == 0)
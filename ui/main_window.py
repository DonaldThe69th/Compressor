"""
main_window.py
--------------
MainWindow with tabs:
  Process  — drop zone + queue + run controls
  Settings — format, resolution, fps, smart compression, output folder
  Advanced — codec, CRF, bitrate, preset, audio
  Enhance  — frame interpolation + upscaling
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QStatusBar, QTabWidget, QFrame
)

from core.job_queue import JobQueue
from core.video_job import VideoJob, JobStatus
from core.video_probe import VideoProbe
from utils.file_utils import FileUtils
from ui.file_drop_widget import FileDropWidget
from ui.job_list_widget import JobListWidget
from ui.basic_settings import BasicSettingsPanel
from ui.advanced_settings import AdvancedSettingsPanel
from ui.interp_panel import InterpPanel
from ui.upscale_panel import UpscalePanel


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._queue = JobQueue(parent=self)
        self._queue.job_started.connect(self._on_job_started)
        self._queue.job_progress.connect(self._on_job_progress)
        self._queue.job_finished.connect(self._on_job_finished)
        self._queue.job_failed.connect(self._on_job_failed)
        self._queue.queue_empty.connect(self._on_queue_empty)

        self._build_ui()
        self.setWindowTitle("Compressor")
        self.resize(820, 640)
        self.setMinimumSize(660, 500)
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.addTab(self._make_process_tab(), "Process")
        self._tabs.addTab(self._make_settings_tab(), "Settings")
        self._tabs.addTab(self._make_advanced_tab(), "Advanced")
        self._tabs.addTab(self._make_enhance_tab(), "Enhance")
        root.addWidget(self._tabs)

        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready — drop video files to begin.")
        self.setStatusBar(self._status_bar)

    def _make_process_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        self._drop_widget = FileDropWidget()
        self._drop_widget.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self._drop_widget)

        self._job_list = JobListWidget()
        self._job_list.job_remove_requested.connect(self._on_remove_job)
        layout.addWidget(self._job_list)

        layout.addWidget(self._make_divider())
        layout.addLayout(self._make_action_bar())
        return tab

    def _make_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        self._basic_settings = BasicSettingsPanel()
        layout.addWidget(self._basic_settings)
        layout.addStretch()
        return tab

    def _make_advanced_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        self._advanced_settings = AdvancedSettingsPanel()
        layout.addWidget(self._advanced_settings)
        layout.addStretch()
        return tab

    def _make_enhance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        self._interp_panel = InterpPanel()
        self._upscale_panel = UpscalePanel()
        layout.addWidget(self._interp_panel)
        layout.addWidget(self._make_divider())
        layout.addWidget(self._upscale_panel)
        layout.addStretch()
        return tab

    def _make_action_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self._start_btn = QPushButton("▶  Start Queue")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.setFixedHeight(34)
        self._start_btn.clicked.connect(self._start_queue)
        self._start_btn.setToolTip("Begin processing all pending jobs")

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(34)
        self._cancel_btn.clicked.connect(self._queue.cancel_current)
        self._cancel_btn.setToolTip("Cancel the currently running job")

        self._clear_btn = QPushButton("Clear Finished")
        self._clear_btn.setFixedHeight(34)
        self._clear_btn.clicked.connect(self._clear_finished)
        self._clear_btn.setToolTip("Remove completed and failed jobs from the list")

        bar.addWidget(self._start_btn)
        bar.addWidget(self._cancel_btn)
        bar.addStretch()
        bar.addWidget(self._clear_btn)
        return bar

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------

    def _on_files_dropped(self, paths: list):
        for path in paths:
            self._add_video(path)

    def _add_video(self, path: str):
        try:
            meta = VideoProbe.probe(path)

            # Build a job with default state first
            job = VideoJob(input_path=path, source_metadata=meta)

            # Apply output settings (format, resolution, fps)
            self._basic_settings.apply_to_job(job)
            # Codec/preset overrides from advanced tab
            self._advanced_settings.apply_to_job(job)
            # Enhance settings
            self._interp_panel.apply_to_job(job)
            self._upscale_panel.apply_to_job(job)

            # Build output path using the resolved format + user folder
            output_folder = self._basic_settings.get_output_folder()
            output_format = job.output_format or "mp4"
            raw_path = FileUtils.build_output_path(
                input_path=path,
                output_folder=output_folder,
                output_format=output_format,
            )
            job.output_path = FileUtils.ensure_unique(raw_path)

            self._queue.add_job(job)
            self._job_list.add_job(
                job,
                default_mode=self._basic_settings.get_default_mode(),
                default_value=self._basic_settings.get_default_value(),
            )
            self._status_bar.showMessage(f"Added: {os.path.basename(path)}")

        except Exception as e:
            QMessageBox.critical(self, "Failed to load file",
                                 f"{os.path.basename(path)}:\n{e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                self._add_video(url.toLocalFile())

    # ------------------------------------------------------------------
    # Queue control
    # ------------------------------------------------------------------

    def _start_queue(self):
        pending = [j for j in self._queue.jobs() if j.status == JobStatus.PENDING]
        if not pending:
            self._status_bar.showMessage("No pending jobs in queue.")
            return
        self._start_btn.setEnabled(False)
        self._queue.start()

    def _clear_finished(self):
        for job in list(self._queue.jobs()):
            if job.status in (JobStatus.DONE, JobStatus.FAILED, JobStatus.CANCELLED):
                self._job_list.remove_job(job)
        self._queue.clear_finished()
        self._status_bar.showMessage("Finished jobs cleared.")

    def _on_remove_job(self, job: VideoJob):
        self._queue.remove_job(job)
        self._job_list.remove_job(job)

    # ------------------------------------------------------------------
    # Queue signals
    # ------------------------------------------------------------------

    def _on_job_started(self, job: VideoJob):
        self._job_list.update_status(job)
        self._status_bar.showMessage(f"Processing: {job.display_name()}")

    def _on_job_progress(self, job: VideoJob, pct: float):
        self._job_list.update_progress(job, pct)

    def _on_job_finished(self, job: VideoJob):
        self._job_list.update_status(job)
        self._status_bar.showMessage(f"Done: {job.display_name()}")

    def _on_job_failed(self, job: VideoJob, error: str):
        self._job_list.update_status(job)
        self._status_bar.showMessage(f"Failed: {job.display_name()}")
        QMessageBox.warning(self, f"Job failed: {job.display_name()}", error)

    def _on_queue_empty(self):
        self._start_btn.setEnabled(True)
        self._status_bar.showMessage("All jobs complete.")
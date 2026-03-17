"""
compression.py
--------------
Size-based compression only.

Two modes:
  - Percentage: reduce file size by X% (e.g. 50% = half the original size)
  - MB: target a specific file size in megabytes

Both use two-pass encoding so FFmpeg actually hits the target accurately.
"""

from dataclasses import dataclass
from typing import Optional
from core.video_probe import VideoMetadata


SPEED_PRESETS = ["veryslow", "slower", "slow", "medium", "fast", "faster", "veryfast"]

CRF_DEFAULTS = {
    "libx264":    26,
    "libx265":    30,
    "libvpx-vp9": 34,
    "libaom-av1": 38,
}


@dataclass
class CompressionPlan:
    codec:               str
    preset:              str
    two_pass:            bool          = True
    target_bitrate_kbps: Optional[int] = None
    reason:              str           = ""


class CompressionEngine:

    def plan_percent(self,
                     meta: VideoMetadata,
                     codec: str,
                     preset: str,
                     reduction_pct: float) -> CompressionPlan:
        """
        Target a percentage reduction from source file size.
        e.g. reduction_pct=50 → output is 50% smaller than source.
        """
        if not meta.file_size:
            raise ValueError("Source file size unknown — cannot compute percentage target.")
        if not 1 <= reduction_pct <= 99:
            raise ValueError(f"Reduction must be 1–99%, got {reduction_pct}%.")

        target_bytes = meta.file_size * (1.0 - reduction_pct / 100.0)
        src_kbps = meta.bitrate / 1000 if meta.bitrate else 0

        return self._plan_from_bytes(
            meta, codec, preset, target_bytes,
            reason=(
                f"{reduction_pct:.0f}% reduction — "
                f"source {meta.file_size / 1024 / 1024:.1f} MB at {src_kbps:.0f} kbps"
            )
        )

    def plan_mb(self,
                meta: VideoMetadata,
                codec: str,
                preset: str,
                target_mb: float) -> CompressionPlan:
        """Target a specific output file size in megabytes."""
        if target_mb <= 0:
            raise ValueError("Target size must be greater than 0 MB.")

        target_bytes = target_mb * 1024 * 1024
        src_mb = meta.file_size / 1024 / 1024 if meta.file_size else 0

        if meta.file_size and target_bytes >= meta.file_size:
            raise ValueError(
                f"Target ({target_mb:.1f} MB) must be smaller than "
                f"the source ({src_mb:.1f} MB)."
            )

        return self._plan_from_bytes(
            meta, codec, preset, target_bytes,
            reason=f"Target {target_mb:.1f} MB — source was {src_mb:.1f} MB"
        )

    def _plan_from_bytes(self,
                         meta: VideoMetadata,
                         codec: str,
                         preset: str,
                         target_bytes: float,
                         reason: str) -> CompressionPlan:
        """
        Back-calculate required video bitrate from target size and duration.

            total_bits = target_bytes × 8
            audio_bits = 128 kbps × duration
            video_kbps = (total_bits − audio_bits) / duration / 1000
        """
        if not meta.duration or meta.duration <= 0:
            raise ValueError("Source duration unknown — cannot compute bitrate target.")

        duration   = meta.duration
        audio_kbps = 128
        video_bits = (target_bytes * 8) - (audio_kbps * 1000 * duration)

        if video_bits <= 0:
            raise ValueError(
                f"Target size is too small to fit the audio track "
                f"({audio_kbps} kbps × {duration:.0f}s)."
            )

        video_kbps = max(50, int(video_bits / duration / 1000))

        return CompressionPlan(
            codec=codec,
            preset=preset,
            two_pass=True,
            target_bitrate_kbps=video_kbps,
            reason=f"{reason} → {video_kbps} kbps video bitrate. Two-pass."
        )
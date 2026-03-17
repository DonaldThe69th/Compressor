"""
format_utils.py
---------------
Codec/container compatibility and display name mapping.

All UI code uses display names (e.g. "H.264").
All FFmpeg code uses internal names (e.g. "libx264").
CODEC_TO_FFMPEG is the single translation table between the two.
"""

# Display name → FFmpeg codec string
CODEC_TO_FFMPEG: dict[str, str] = {
    "H.264":    "libx264",
    "H.265":    "libx265",
    "VP9":      "libvpx-vp9",
    "AV1":      "libaom-av1",
    "WMV":      "wmv2",
    "Copy":     "copy",
}

# FFmpeg codec string → display name (reverse lookup)
FFMPEG_TO_CODEC: dict[str, str] = {v: k for k, v in CODEC_TO_FFMPEG.items()}

# Container format → supported display-name codecs
CONTAINER_CODEC_MAP: dict[str, list[str]] = {
    "mp4":  ["H.264", "H.265", "AV1", "Copy"],
    "mkv":  ["H.264", "H.265", "VP9", "AV1", "Copy"],
    "webm": ["VP9", "AV1"],
    "avi":  ["H.264", "Copy"],
    "mov":  ["H.264", "H.265", "Copy"],
    "flv":  ["H.264", "Copy"],
    "wmv":  ["WMV", "Copy"],
}


def to_ffmpeg(display_name: str) -> str:
    """Convert a display codec name to its FFmpeg string. Returns as-is if unknown."""
    return CODEC_TO_FFMPEG.get(display_name, display_name)


def to_display(ffmpeg_name: str) -> str:
    """Convert an FFmpeg codec string to its display name. Returns as-is if unknown."""
    return FFMPEG_TO_CODEC.get(ffmpeg_name, ffmpeg_name)


def compatible_codecs(container: str) -> list[str]:
    """Return display-name codecs compatible with a given container."""
    return CONTAINER_CODEC_MAP.get(container.lower(), [])


def all_supported_formats() -> list[str]:
    return list(CONTAINER_CODEC_MAP.keys())
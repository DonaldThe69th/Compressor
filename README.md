# Compressor

Professional desktop video compression and enhancement tool built with Python, PyQt6, and FFmpeg.

Compressor is designed for creators, editors, students, and developers who need a practical local workflow for reducing video size, changing output settings, upscaling footage, and generating smoother frame rates without relying on cloud processing. The application provides a graphical queue-based interface over FFmpeg, with optional AI-powered enhancement tools such as RIFE for frame generation and Real-ESRGAN for upscaling.

## Project Summary

Compressor focuses on local, controllable video processing:

- Batch-oriented desktop workflow with a PyQt6 user interface.
- FFmpeg-based encoding, resizing, format conversion, audio handling, and frame extraction.
- Smart compression advisor using video metadata heuristics.
- Optional frame interpolation through RIFE NCNN Vulkan.
- Optional AI upscaling through Real-ESRGAN NCNN Vulkan.
- Built-in fallback paths for non-AI processing, including Lanczos upscaling and FFmpeg interpolation.
- Organized AI model folders for easier maintenance, packaging, and cleanup.

## Key Features

- **Video compression:** reduce file size by percentage or target output size.
- **Codec control:** configure video codec, audio codec, CRF, preset, bitrate, and format.
- **Resolution control:** keep original size, resize, or upscale to selected dimensions.
- **Frame generation:** use FFmpeg interpolation or bundled RIFE models for 2x frame generation.
- **AI upscaling:** use Real-ESRGAN when bundled or available on `PATH`.
- **Queue management:** process multiple jobs with status tracking and progress reporting.
- **Source probing:** inspect metadata such as codec, resolution, bitrate, duration, and FPS.
- **Local-first workflow:** videos are processed on the user's machine.

## Technology Stack

- **Language:** Python
- **UI framework:** PyQt6
- **Video engine:** FFmpeg / ffprobe
- **AI frame generation:** RIFE NCNN Vulkan, optional
- **AI upscaling:** Real-ESRGAN NCNN Vulkan, optional
- **Packaging target:** desktop application workflow

## Requirements

Install the Python dependencies from `Requirements.txt`:

```bash
pip install -r Requirements.txt
```

The current Python package requirements are:

```text
ffmpeg-python>=0.2.0
PyQt6>=6.6.0
```

FFmpeg and ffprobe must be installed separately or bundled with the application. They should be available through the system `PATH` or through the app's configured tool lookup paths.

## Running the Application

From the `Compressor/` application directory:

```bash
python Main.py
```

Recommended local workflow:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r Requirements.txt
python Main.py
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Bundled AI Tools

The app can use bundled external binaries for higher-quality enhancement, so end users do not need to install them manually if the tools are shipped with the app.

Preferred AI tool layout:

```text
Compressor/
  ai/
    frame_generation/
      rife/
        rife-ncnn-vulkan.exe
        *.bin
        *.param
    upscaling/
      realesrgan/
        realesrgan-ncnn-vulkan.exe
        *.bin
        *.param
```

The app checks these local folders before falling back to the system `PATH`. Legacy `ai/<tool>/` and `tools/<tool>/` lookups are still supported for older setups, but the grouped `ai/` folders are the preferred bundled location.

## Project Structure

```text
Compressor/
  Main.py                  Application entry point
  Requirements.txt         Python dependencies
  README.md                Project documentation
  ai/                      AI helpers and bundled model/tool assets
    frame_generation/      RIFE and future frame-generation assets
    upscaling/             Real-ESRGAN and future upscaling assets
  assets/                  Stylesheets and UI assets
  config/                  Default application settings
  core/                    Video jobs, probing, compression, FFmpeg worker logic
  ui/                      PyQt6 widgets, panels, and main window
  utils/                   Logging, file helpers, and external tool resolution
  tests/                   Test area
  todo/                    Planning notes and request tracking
```

## Architecture Notes

The application is separated into practical layers:

- **UI layer:** collects user choices, shows job controls, and keeps the desktop workflow responsive.
- **Core layer:** owns video jobs, compression settings, interpolation settings, upscaling settings, and worker execution.
- **Tool resolution layer:** finds bundled enhancement binaries first, then falls back to legacy folders and system `PATH`.
- **AI asset layer:** stores optional third-party model binaries in clearly separated feature folders.

This structure keeps large AI assets away from normal application code and makes it easier to add, replace, or remove models without touching the main processing pipeline.

## Configuration

Default settings live in:

```text
config/defaults.json
```

These defaults cover video codec, CRF, preset, output format, audio behavior, compression mode, interpolation, upscaling, output naming, and queue behavior.

## Development Notes

Useful validation commands:

```bash
python -m compileall .
python Main.py
```

If FFmpeg-related processing fails, confirm that:

- `ffmpeg` is available from the terminal.
- `ffprobe` is available from the terminal.
- Optional AI binaries are placed in the expected `ai/` subfolders or available on `PATH`.
- The selected model name exists inside the bundled tool folder.

## Credentials and Attribution

Project identity:

- **Project name:** Compressor
- **Application type:** desktop video compression and enhancement tool
- **Primary implementation:** Python, PyQt6, FFmpeg integration
- **AI enhancement support:** optional local RIFE and Real-ESRGAN integrations

Third-party technology acknowledgements:

- **FFmpeg / ffprobe:** used for video probing, transcoding, frame extraction, filtering, and muxing.
- **PyQt6:** used for the desktop application interface.
- **RIFE NCNN Vulkan:** optional frame-generation backend. The bundled RIFE copy in this repository includes its own MIT license file under `ai/frame_generation/rife/LICENSE`.
- **Real-ESRGAN NCNN Vulkan:** optional AI upscaling backend when bundled or installed separately.

## Rights and Licensing

Unless a separate license file is added to this repository, the original Compressor application source code should be treated as proprietary or all-rights-reserved by the project owner. Do not redistribute, sublicense, or publish the original project source without permission from the rights holder.

Third-party components remain under their own licenses and ownership terms. Bundling or referencing a third-party binary, model, framework, or library does not transfer ownership of that component to this project.

When distributing builds of this application, include all required notices and license files for bundled third-party components, including but not limited to FFmpeg, PyQt6, RIFE, Real-ESRGAN, and any AI model files shipped with the release.

## Distribution Checklist

Before sharing a packaged build:

- Confirm FFmpeg and ffprobe licensing obligations for the specific binaries being distributed.
- Include third-party license files for every bundled tool and model.
- Verify that the AI model folders only contain files you have the right to redistribute.
- Test the app on a clean machine without developer-only environment paths.
- Confirm that large model files are intentionally included or intentionally excluded.
- Update this README if folder names, tool names, supported models, or packaging behavior changes.

## Disclaimer

Compressor is provided as a local video-processing utility. Output quality, file size, encoding speed, GPU compatibility, and AI enhancement results depend on source media, selected settings, installed binaries, hardware, drivers, and model availability. Always keep backups of source videos before processing.

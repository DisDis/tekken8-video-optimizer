# Tekken 8 Video Optimizer
A script to drastically reduce disk space usage in Tekken 8 by replacing all .usm video files with minimal stubs.

**Result: ~47 GB → ~0.1 GB saved** from video files.

# What This Script Does
Tekken 8 stores cutscenes and UI videos in .usm format (CRI Sofdec), which can take up tens of gigabytes. This script:
1. Scans all .usm files in the game's Movies directory
2. Extracts the original resolution and internal stream name from each file
3. Generates a 1-second green-screen video (for easy visual debugging) in MPEG-1 format at the original resolution and 60 FPS
4. Packages it into a valid .usm container using the cricodecs library
5. Replaces the original file after creating a backup

The Unreal Engine 5 in Tekken 8 accepts these stubs correctly, allowing you to play the game with minimal disk footprint.

# System Requirements
* OS: Linux (tested on Ubuntu/Debian)
* Python: 3.9 or higher
* FFmpeg: (with mpeg1video support)
* Python library: cricodecs

# Installation
1. Install system dependencies
```bash
sudo apt update
sudo apt install ffmpeg python3-pip
```
2. Install the cricodecs library
```bash
pip3 install cricodecs
```
3. Clone the repository
```bash
git clone https://github.com/DisDis/tekken8-video-optimizer.git
cd tekken8-video-optimizer
```

# Configuration
Open the optimize.py file in any text editor and change the path to your Tekken 8 installation in the GAME_ROOT adn STUB_DIR variable:
```python
GAME_ROOT = Path("/path/to/your/games/TEKKEN 8")
STUB_DIR = Path("/tmp/defs_t8_stubs")
```
The script expects the following directory structure:
```text
TEKKEN 8/
└── Polaris/
└── Content/
└── Movies/
└── usm/ ← .usm files are here
├── Story/
├── CharEpisode/
└── ...
```
# Usage
First run (replace all videos)
```bash
python3 optimize.py
```

The script will:

* Create a backup_original_usm folder and move all processed originals there
* Replace each video with a ~500 KB – 1 MB stub
* Print a summary (how many files processed and skipped)
* Subsequent runs
* The script is safe to run multiple times. It automatically skips already-processed files by checking:
  Whether a backup exists in the backup_original_usm folder
  File size (if less than 1 MB, it's considered a stub)

Original Tekken 8 files don't contain audio tracks in USM

# Troubleshooting

Error Library 'cricodecs' not found: Make sure you installed the library for the correct Python version (python3 -m pip install cricodecs)

Error FFmpeg not found: Make sure FFmpeg is installed and available in system PATH (ffmpeg -version)

# Disclaimer
This tool is intended for personal use to save disk space. The script automatically creates backups of original files, but use it at your own risk.

# License
MIT
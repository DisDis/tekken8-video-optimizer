import os
import subprocess
import shutil
import sys
from pathlib import Path

try:
    from cricodecs import usm
except ImportError:
    print("[ERROR] Library 'cricodecs' not found!", file=sys.stderr)
    print("[ERROR] Install it with: pip3 install cricodecs", file=sys.stderr)
    sys.exit(1)

# === PATH CONFIGURATION (Linux) ===
GAME_ROOT = Path("/home/USER/games/TEKKEN 8")
UNPACKED_MOVIES_DIR = GAME_ROOT / "Polaris/Content/Movies/usm"

FFMPEG_BIN = Path("ffmpeg")

STUB_DIR = Path("/tmp/defs_t8_stubs")
UNPACKED_BACKUP = UNPACKED_MOVIES_DIR / "backup_original_usm"

HALT_ON_ERROR: bool = True

# Size threshold: files smaller than this are considered already stubbed
STUB_SIZE_THRESHOLD: int = 1000000  # 1 MB

def log_info(msg: str) -> None: print(f"[INFO] {msg}")
def log_warn(msg: str) -> None: print(f"[WARN] {msg}")
def log_error(msg: str) -> None: print(f"[ERROR] {msg}", file=sys.stderr)

def cleanup() -> None:
    log_info("Cleaning up temporary directories...")
    if STUB_DIR.is_dir(): shutil.rmtree(STUB_DIR)

def check_tools() -> bool:
    if not shutil.which(str(FFMPEG_BIN)):
        log_error(f"FFmpeg not found in PATH.")
        return False
    return True

def is_already_stubbed(usm_path: Path) -> bool:
    """Checks if the file has already been replaced with a stub"""
    # Check 1: Backup of original exists — file already processed
    backup_path = UNPACKED_BACKUP / usm_path.name
    if backup_path.is_file():
        return True
    
    # Check 2: File size is below threshold — this is a stub
    if usm_path.stat().st_size < STUB_SIZE_THRESHOLD:
        return True
    
    return False

def encode_usm_stub(src_file: Path, dst_file: Path) -> bool:
    """Creates a USM stub with original resolution and 1 second duration"""
    log_info(f"  [DEBUG] Starting processing: {src_file.name}")
    
    original_filename = None
    original_width = None
    original_height = None
    
    try:
        original_movie = usm.load(str(src_file))
        if original_movie.streams and len(original_movie.streams) > 0:
            stream_info = original_movie.streams[0]
            original_filename = stream_info.filename
            log_info(f"  [DEBUG] Original internal name: {original_filename}")
    except Exception as e:
        log_warn(f"  [DEBUG] Failed to extract name from cricodecs: {e}")
    
    try:
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            str(src_file)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        output = result.stdout.strip()
        
        if output and ',' in output:
            parts = output.split(',')
            if len(parts) >= 2:
                try:
                    original_width = int(parts[0].strip())
                    original_height = int(parts[1].strip())
                    log_info(f"  [DEBUG] Original resolution: {original_width}x{original_height}")
                except ValueError:
                    pass
    except Exception as e:
        log_warn(f"  [DEBUG] ffprobe error: {e}")
    
    if not original_width or not original_height:
        original_width = 2816
        original_height = 1584
    
    target_width = original_width
    target_height = original_height
    fps = 60
    total_frames = int(1.0 * fps)
    
    log_info(f"  [DEBUG] Frames: {total_frames}, FPS: {fps}, Size: {target_width}x{target_height}")
    
    temp_m1v = STUB_DIR / "stub_video.m1v"
    if temp_m1v.is_file(): temp_m1v.unlink()
    if dst_file.is_file(): dst_file.unlink()

    ffmpeg_cmd = [
        str(FFMPEG_BIN), "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c=green:s={target_width}x{target_height}:r={fps}",
        "-frames:v", str(total_frames),
        "-c:v", "mpeg1video",
        "-pix_fmt", "yuv420p",
        "-b:v", "5000k",
        "-g", "12",
        "-bf", "2",
        "-f", "mpeg1video",
        str(temp_m1v)
    ]
    
    try:
        res_ffmpeg = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_ffmpeg.returncode != 0:
            log_error(f"  [DEBUG] FFmpeg crashed: {res_ffmpeg.stderr.strip()}")
            return False
    except Exception as e:
        log_error(f"  [DEBUG] Failed to start ffmpeg: {e}")
        return False

    if not temp_m1v.is_file() or temp_m1v.stat().st_size == 0:
        log_error("  [DEBUG] MPEG-1 file not created!")
        return False
        
    log_info(f"  [DEBUG] Raw MPEG-1 created. Size: {temp_m1v.stat().st_size} bytes.")

    try:
        config_kwargs = {
            "video_path": str(temp_m1v),
            "audio_tracks": [],
            "subtitle_tracks": [],
            "key": None,
            "encrypt_audio": False
        }
        
        if original_filename:
            config_kwargs["video_filename"] = original_filename
        
        config = usm.UsmMuxConfig(**config_kwargs)
        usm.mux(config, str(dst_file))
        
    except Exception as e:
        log_error(f"  [DEBUG] USM packaging error: {e}")
        if temp_m1v.is_file(): temp_m1v.unlink()
        return False

    if temp_m1v.is_file():
        temp_m1v.unlink()
        
    if not dst_file.is_file() or dst_file.stat().st_size == 0:
        log_error(f"  [DEBUG] CRITICAL: USM file not created!")
        return False

    log_info(f"  [DEBUG] SUCCESS: {dst_file.name} created ({dst_file.stat().st_size} bytes)")
    return True

def process_unpacked_movies() -> None:
    if not UNPACKED_MOVIES_DIR.is_dir():
        log_warn("Unpacked movies directory not found.")
        return

    log_info("--- Analyzing external .usm files ---")
    UNPACKED_BACKUP.mkdir(parents=True, exist_ok=True)

    skipped_count = 0
    processed_count = 0

    for root, _, files in os.walk(UNPACKED_MOVIES_DIR):
        if "backup_original_usm" in root:
            continue
            
        for file in files:
            if not file.lower().endswith(".usm"):
                continue
                
            full_path = Path(root) / file
            
            if is_already_stubbed(full_path):
                skipped_count += 1
                continue

            log_info(f"Rebuilding external video: {file}")
            backup_path = UNPACKED_BACKUP / file
            
            shutil.move(str(full_path), str(backup_path))
            
            if not encode_usm_stub(backup_path, full_path):
                log_error(f"Critical encoding error for {file}. Rolling back original.")
                if full_path.is_file(): full_path.unlink()
                shutil.move(str(backup_path), str(full_path))
                
                if HALT_ON_ERROR:
                    log_error("HALT_ON_ERROR flag is active. Process forcibly stopped.")
                    cleanup()
                    sys.exit(1)
            else:
                processed_count += 1

    log_info(f"--- Summary: processed {processed_count}, skipped {skipped_count} (already stubs) ---")

def main() -> None:
    if not check_tools():
        sys.exit(1)
        
    STUB_DIR.mkdir(parents=True, exist_ok=True)
    
    process_unpacked_movies()
    
    cleanup()
    log_info("=== Optimization script completed successfully! ===")

if __name__ == "__main__":
    main()

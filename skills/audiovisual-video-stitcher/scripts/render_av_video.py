#!/usr/bin/env python3
"""
render_av_video.py - Universal Audio-Visual & Slideshow MP4 Video Production Engine

A system-agnostic, zero-external-dependency CLI tool and Python module for stitching
audio tracks (podcasts, monographs, tutorials, talk shows) with single hero images or
multi-image slideshows into broadcast-quality H.264 MP4 videos.

Key Features:
- System & Username Agnostic: Resolves paths dynamically across Linux, macOS, and Windows.
- Standard Library Only: Requires only Python 3 and FFmpeg/FFprobe in system PATH.
- Single Still-Image Mode: Uses FFmpeg stillimage tuning for rapid, low-CPU rendering.
- Multi-Image Slideshow: Automatically synchronizes slide durations to match audio length.
- Aspect Ratios & Letterboxing: Supports 4:3, 16:9, 1:1, and 9:16 with automatic aspect-preserving padding.
- Batch Processing: Built-in concurrent worker pool for batch JSON manifests.
"""

import os
import sys
import argparse
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Canonical Resolution Map
ASPECT_RATIOS = {
    "4:3": "1280:960",      # Botanical monographs, classical art & portraits
    "16:9": "1920:1080",    # Standard widescreen HD / YouTube desktop
    "1:1": "1080:1080",     # Square format / Instagram / Album art
    "9:16": "1080:1920",    # Vertical video / YouTube Shorts / TikTok / Reels
}

def check_dependencies():
    """Verify that ffmpeg and ffprobe are installed and accessible."""
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if not shutil.which("ffprobe"):
        missing.append("ffprobe")
    
    if missing:
        sys.stderr.write(f"[ERROR] Required external tool(s) missing from PATH: {', '.join(missing)}\n")
        sys.stderr.write("Please install them using your system package manager:\n")
        sys.stderr.write("  - Debian/Ubuntu: sudo apt update && sudo apt install -y ffmpeg\n")
        sys.stderr.write("  - macOS: brew install ffmpeg\n")
        sys.stderr.write("  - Windows: winget install Gyan.FFmpeg or choco install ffmpeg\n")
        sys.exit(1)

def get_default_videos_dir():
    """Dynamically determine the canonical Videos directory for the current user/OS."""
    # Check XDG user dir if on Linux
    xdg_videos = os.environ.get("XDG_VIDEOS_DIR")
    if xdg_videos and os.path.isdir(xdg_videos):
        return Path(xdg_videos)
    
    home_videos = Path.home() / "Videos"
    try:
        home_videos.mkdir(parents=True, exist_ok=True)
        return home_videos
    except OSError:
        # Fallback to local 'videos' directory if user home is restricted
        local_videos = Path.cwd() / "videos"
        local_videos.mkdir(parents=True, exist_ok=True)
        return local_videos

def get_media_duration(audio_path):
    """Retrieve exact duration of audio in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(audio_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to probe audio duration for '{audio_path}': {res.stderr.strip()}")
    try:
        data = json.loads(res.stdout)
        return float(data['format']['duration'])
    except (ValueError, KeyError) as e:
        raise RuntimeError(f"Could not parse duration from ffprobe output: {e}")

def resolve_path(path_str):
    """Safely expand user and resolve path."""
    if not path_str:
        return None
    expanded = os.path.expanduser(os.path.expandvars(str(path_str)))
    return Path(expanded).resolve()

def render_single_image(image_path, audio_path, output_path, resolution="1280:960", threads=2, crf=18):
    """Render static image looped with audio track using libx264 stillimage tuning."""
    image_file = resolve_path(image_path)
    audio_file = resolve_path(audio_path)
    output_file = resolve_path(output_path)

    if not image_file.is_file():
        raise FileNotFoundError(f"Image file not found: {image_file}")
    if not audio_file.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    video_filter = (
        f"scale={resolution}:force_original_aspect_ratio=decrease,"
        f"pad={resolution}:(ow-iw)/2:(oh-ih)/2,"
        f"format=yuv420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", "1",
        "-i", str(image_file),
        "-i", str(audio_file),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "fast",
        "-crf", str(crf),
        "-threads", str(threads),
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", video_filter,
        "-shortest",
        str(output_file)
    ]

    print(f"[RENDER] Starting single still-image render -> {output_file.name}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        sys.stderr.write(f"[FFMPEG ERROR] {res.stderr}\n")
        return False
    return True

def render_slideshow(image_paths, audio_path, output_path, resolution="1280:960", threads=2, crf=18):
    """Render multi-image timed slideshow synchronized with audio track."""
    resolved_images = [resolve_path(img) for img in image_paths]
    for img in resolved_images:
        if not img.is_file():
            raise FileNotFoundError(f"Slideshow image not found: {img}")

    audio_file = resolve_path(audio_path)
    if not audio_file.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    output_file = resolve_path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    total_duration = get_media_duration(audio_file)
    num_images = len(resolved_images)
    slide_duration = total_duration / num_images

    print(f"[RENDER] Total audio duration: {total_duration:.2f}s across {num_images} slides ({slide_duration:.2f}s per slide)")

    # Prepare concat demuxer manifest
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        concat_file = f.name
        for img in resolved_images:
            # Escape single quotes in path for ffmpeg concat
            escaped_path = str(img).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
            f.write(f"duration {slide_duration:.4f}\n")
        # FFmpeg concat requires repeating the last file entry
        last_escaped = str(resolved_images[-1]).replace("'", "'\\''")
        f.write(f"file '{last_escaped}'\n")

    video_filter = (
        f"scale={resolution}:force_original_aspect_ratio=decrease,"
        f"pad={resolution}:(ow-iw)/2:(oh-ih)/2,"
        f"format=yuv420p"
    )

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-i", str(audio_file),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(crf),
            "-threads", str(threads),
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", video_filter,
            "-shortest",
            str(output_file)
        ]

        print(f"[RENDER] Processing slideshow concat -> {output_file.name}")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            sys.stderr.write(f"[FFMPEG ERROR] {res.stderr}\n")
            return False
        return True
    finally:
        if os.path.exists(concat_file):
            try:
                os.remove(concat_file)
            except OSError:
                pass

def process_batch_manifest(manifest_path, max_workers=2):
    """Run batch rendering from a JSON manifest file using multiprocessing."""
    manifest_file = resolve_path(manifest_path)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Batch manifest file not found: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    if not isinstance(jobs, list):
        raise ValueError("Batch manifest must be a JSON array of job objects.")

    print(f"[BATCH] Loaded {len(jobs)} jobs from manifest. Running with {max_workers} worker threads.")

    def run_job(job):
        title = job.get("title", "Untitled")
        images = job.get("images", [])
        if isinstance(images, str):
            images = [images]
        audio = job.get("audio")
        aspect = job.get("aspect", "4:3")
        res = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["4:3"])
        
        output = job.get("output")
        if not output:
            default_dir = get_default_videos_dir()
            clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
            output = str(default_dir / f"{clean_title}.mp4")

        try:
            if len(images) == 1:
                ok = render_single_image(images[0], audio, output, resolution=res)
            else:
                ok = render_slideshow(images, audio, output, resolution=res)
            return (title, output, ok, None)
        except Exception as err:
            return (title, output, False, str(err))

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_job, job): job for job in jobs}
        for future in as_completed(futures):
            title, out_path, success, err = future.result()
            if success:
                print(f"[BATCH SUCCESS] ✓ {title} -> {out_path}")
            else:
                print(f"[BATCH FAILURE] ✗ {title}: {err}")
            results.append((title, success, err))

    total = len(results)
    succeeded = sum(1 for _, s, _ in results if s)
    print(f"\n[BATCH COMPLETED] {succeeded}/{total} videos rendered successfully.")
    return succeeded == total

def main():
    check_dependencies()

    parser = argparse.ArgumentParser(
        description="Universal Audio-Visual MP4 Video Generator for Antigravity CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Single still-image podcast video (4:3 portrait)
  render_av_video.py --images hero.jpg --audio podcast.mp3 --output ~/Videos/Episode1.mp4

  # Multi-image slideshow automatically timed to audio (16:9 widescreen)
  render_av_video.py --images p1.jpg p2.jpg p3.jpg --audio narration.wav --aspect 16:9 --title "Landscape Documentary"

  # Batch render from JSON manifest
  render_av_video.py --batch manifest.json --workers 3
"""
    )

    parser.add_argument("--images", nargs="+", help="Path to one or more image files (jpg, png, webp)")
    parser.add_argument("--audio", help="Path to the audio file (.mp3 / .wav / .m4a)")
    parser.add_argument("--output", help="Destination output .mp4 path (defaults to ~/Videos/<title>.mp4)")
    parser.add_argument("--title", help="Canonical title for video (used for default filename if --output omitted)")
    parser.add_argument("--aspect", choices=list(ASPECT_RATIOS.keys()), default="4:3",
                        help="Target aspect ratio: 4:3 (1280x960), 16:9 (1920x1080), 1:1 (1080x1080), 9:16 (1080x1920). Default: 4:3")
    parser.add_argument("--threads", type=int, default=2, help="FFmpeg CPU threads per process (default: 2)")
    parser.add_argument("--crf", type=int, default=18, help="H.264 visual quality factor (default: 18 - visually lossless)")
    parser.add_argument("--batch", help="Path to a JSON manifest file containing multiple rendering jobs")
    parser.add_argument("--workers", type=int, default=2, help="Concurrent workers for batch processing (default: 2)")

    args = parser.parse_args()

    # Batch Mode
    if args.batch:
        success = process_batch_manifest(args.batch, max_workers=args.workers)
        sys.exit(0 if success else 1)

    # Single or Slideshow Mode
    if not args.images or not args.audio:
        parser.error("Both --images and --audio are required when not using --batch mode.")

    resolution = ASPECT_RATIOS[args.aspect]

    # Resolve output path
    if args.output:
        dest_path = resolve_path(args.output)
    else:
        out_dir = get_default_videos_dir()
        if args.title:
            clean_title = "".join(c for c in args.title if c.isalnum() or c in (" ", "-", "_")).strip()
            dest_path = out_dir / f"{clean_title}.mp4"
        else:
            audio_stem = Path(args.audio).stem
            dest_path = out_dir / f"{audio_stem}.mp4"

    try:
        if len(args.images) == 1:
            success = render_single_image(
                args.images[0], args.audio, dest_path,
                resolution=resolution, threads=args.threads, crf=args.crf
            )
        else:
            success = render_slideshow(
                args.images, args.audio, dest_path,
                resolution=resolution, threads=args.threads, crf=args.crf
            )

        if success:
            print(f"\n[SUCCESS] Generated video at: {dest_path}")
            sys.exit(0)
        else:
            print(f"\n[FAILED] Video generation failed for: {dest_path}")
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"\n[FATAL ERROR] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

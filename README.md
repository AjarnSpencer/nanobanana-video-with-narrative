# 🍌 Nanobanana Video with Narrative (`nanobanana-video-with-narrative`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FFmpeg: Required](https://img.shields.io/badge/FFmpeg-Required-red.svg)](https://ffmpeg.org/)
[![CLI: Antigravity & Gemini](https://img.shields.io/badge/CLI-Antigravity%20%7C%20Gemini-purple.svg)](https://github.com/google-gemini)

A portable, cross-platform **Skill & Plugin** for **Google Antigravity CLI** (`agy`). It seamlessly pairs **Nanobanana** / Imagen visual plates, multi-image slideshow galleries, and spoken audio narratives (podcasts, monographs, tutorials, talk shows) into broadcast-grade `.mp4` video productions using FFmpeg with zero external Python library dependencies.

Supports both **single still-image featured artwork** (using ultra-efficient H.264 still-image tuning) and **dynamic multi-image story plates** automatically timed and synchronized to speech duration.

---

## 🏛 Architecture

```mermaid
graph TD
    UserPrompt([User Prompt / Batch Manifest]) --> Engine{render_av_video.py}
    
    subgraph Nanobanana Visuals
        PlateSingle[Nanobanana Hero Plate]
        PlateMulti[Multi-Plate Story Slideshow]
    end

    subgraph Spoken Narrative
        AudioIn[Neural TTS / Podcast Narration Track]
    end

    PlateSingle --> Engine
    PlateMulti --> Engine
    AudioIn --> Engine

    subgraph Processing Engine
        Engine --> DurationProbe[ffprobe: Audio Duration Probe]
        DurationProbe --> ConcatMath[Even Slide Duration Divider]
        ConcatMath --> AspectScaler[Aspect Ratio Preserver & Auto Letterbox]
        AspectScaler --> FFmpegCore[FFmpeg libx264 Still-Image & AAC 192k]
    end

    FFmpegCore --> VideoOut[Broadcast-Ready MP4 Video]
    VideoOut --> Syndication[YouTube & Multi-Platform Syndication]
```

---

## 🌟 Key Features

- **System & Username Agnostic:** Resolves paths dynamically across Linux, macOS, and Windows with zero hardcoded environment paths.
- **Zero Python Dependencies:** Uses only Python standard library modules (`os`, `sys`, `subprocess`, `argparse`, `json`, `pathlib`, `concurrent.futures`).
- **Single Hero Image Tuning:** Applies `-c:v libx264 -tune stillimage -crf 18 -threads 2` to render high-fidelity podcast videos with minimal CPU and small file sizes.
- **Automated Slideshow Synchronization:** Probes audio duration via `ffprobe`, calculates $\text{Slide Duration} = \frac{\text{Total Duration}}{\text{Image Count}}$, and stitches images sequentially with concat demuxing.
- **Universal Aspect Ratio Matrix:** Automatically prevents distortion or warping by applying clean letterbox or pillarbox padding.
- **Concurrent Batch Engine:** Includes built-in multi-process worker pool (`--batch manifest.json --workers 2`) for bulk rendering.
- **Antigravity CLI Native:** Fully validated with `agy plugin validate --strict`.

---

## 📐 Aspect Ratio Matrix

| Aspect Ratio | Resolution | Best Suited For | Auto-Padding Behavior |
| :---: | :---: | :--- | :--- |
| **`4:3`** | `1280x960` | Classical art, amulet portraits, botanical monographs, Nanobanana 4:3 plates | Preserves 4:3 canvas with clean borders |
| **`16:9`** | `1920x1080` | Standard YouTube widescreen, documentary landscapes | Full HD 1080p canvas with auto-pillarboxing |
| **`1:1`** | `1080x1080` | Instagram feed posts, square album artwork | 1:1 square canvas |
| **`9:16`** | `1080x1920` | YouTube Shorts, TikTok, Instagram Reels | Vertical full HD mobile canvas |

---

## 🚀 Installation

### Option 1: Install as an Antigravity Plugin (Recommended)

Clone the repository directly into your global or project plugins directory:

```bash
# Global installation (available everywhere in Antigravity CLI)
git clone https://github.com/AjarnSpencer/nanobanana-video-with-narrative.git \
  ~/.gemini/config/plugins/nanobanana-video-with-narrative

# Validate plugin
agy plugin validate ~/.gemini/config/plugins/nanobanana-video-with-narrative --strict
```

### Option 2: Install as a Workspace Skill

If you want the skill available in a specific project or workspace:

```bash
mkdir -p .agents/skills
git clone https://github.com/AjarnSpencer/nanobanana-video-with-narrative.git /tmp/nb-video
cp -r /tmp/nb-video/skills/nanobanana-video-with-narrative .agents/skills/
rm -rf /tmp/nb-video
```

### Option 3: Standalone CLI Usage

Clone anywhere and run the script directly:

```bash
git clone https://github.com/AjarnSpencer/nanobanana-video-with-narrative.git
cd nanobanana-video-with-narrative
python3 skills/nanobanana-video-with-narrative/scripts/render_av_video.py --help
```

---

## 🛠 Prerequisites

Requires `ffmpeg` and `ffprobe` installed on your system:

- **Debian / Ubuntu:**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
- **macOS (Homebrew):**
  ```bash
  brew install ffmpeg
  ```
- **Windows (winget / Chocolatey):**
  ```powershell
  winget install Gyan.FFmpeg
  # or
  choco install ffmpeg
  ```

---

## 📖 Usage Examples

### 1. Within Antigravity CLI (TUI / Slash Command)

You can invoke the skill directly in natural language or with flags:

```text
/nanobanana-video-with-narrative --images plate1.jpg plate2.jpg --audio narration.mp3 --output ~/Videos/Story.mp4 --aspect 4:3
```

Or ask the agent conversationally:
```text
Stitch my narrative audio at ~/Music/chapter1.mp3 with the 4 Nanobanana plates in ~/Pictures/story/ into a 4:3 video.
```

### 2. Standalone Terminal Command

#### Single Still-Image Video (4:3 Portrait)
```bash
python3 skills/nanobanana-video-with-narrative/scripts/render_av_video.py \
  --images ~/Pictures/nanobanana_hero.jpg \
  --audio ~/Music/narrative_audio.mp3 \
  --aspect 4:3 \
  --output ~/Videos/Nanobanana_Episode_01.mp4
```

#### Multi-Plate Synchronized Slideshow (16:9 Widescreen)
```bash
python3 skills/nanobanana-video-with-narrative/scripts/render_av_video.py \
  --images plate1.jpg plate2.jpg plate3.jpg plate4.jpg \
  --audio narrative_track.wav \
  --aspect 16:9 \
  --title "Sacred Art Retrospective"
```

#### Batch Processing via JSON Manifest
```bash
python3 skills/nanobanana-video-with-narrative/scripts/render_av_video.py \
  --batch skills/nanobanana-video-with-narrative/examples/batch_manifest.example.json \
  --workers 3
```

---

## 📋 Batch Manifest Schema

```json
[
  {
    "title": "Ancient Temple Bells - Episode 01",
    "images": [
      "~/Pictures/plate_entrance.jpg",
      "~/Pictures/plate_bell_tower.jpg",
      "~/Pictures/plate_meditation_hall.jpg"
    ],
    "audio": "~/Music/episode_01.mp3",
    "aspect": "16:9",
    "output": "~/Videos/Ancient Temple Bells - Episode 01.mp4"
  },
  {
    "title": "Botanical Terpene Retrospective",
    "images": [
      "~/Pictures/botanical_plate_01.jpg"
    ],
    "audio": "~/Music/botanical_guide.mp3",
    "aspect": "4:3"
  }
]
```

---

## ⚖️ YouTube Compliance & Safe Syndication

When publishing generated videos to platforms like YouTube:

1. **Category:** Use Category `28` (*Science & Technology*) or `27` (*Education*).
2. **Harm Reduction & Education Notice:** If covering sensitive botanical, herbal, or esoteric traditions, include a prominent educational statement in the description:
   > *Educational & Botanical Documentary: An informational historical retrospective exploring the geographical origin, agricultural evolution, terpene chemistry, and cultural history of [Topic/Entity]. Produced exclusively for botanical, historical, and harm-reduction educational purposes.*
3. **Outbound Linking:** Point links to encyclopedia monographs or educational documentation rather than direct commercial shopping carts.

---

## 📄 License

Released under the [MIT License](LICENSE). Copyright (c) 2026 Ajarn Spencer Littlewood.

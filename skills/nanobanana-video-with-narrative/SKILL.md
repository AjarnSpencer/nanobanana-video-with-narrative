---
name: nanobanana-video-with-narrative
description: >-
  Universal audio-visual production suite for stitching Nanobanana visuals, multi-image slideshow plates,
  and spoken audio narratives into broadcast-ready MP4 videos. Features FFmpeg still-image tuning,
  dynamic multi-slide duration calculations, and YouTube EDSA compliance safeguards.
---

# Nanobanana Video with Narrative (`nanobanana-video-with-narrative`)

This skill provides complete operational recipes, FFmpeg configurations, and automated Python pipelines for turning Nanobanana / Imagen visual plates and spoken audio narratives (podcasts, monographs, tutorials, talk shows) into high-definition `.mp4` video files for YouTube broadcasting, social syndication, and digital archives.

---

## 1. Single Hero Image Video Generation

When a narrative track has a single featured Nanobanana plate (e.g., a 4:3 art portrait, botanical specimen, or hero banner):

### FFmpeg Command Recipe
```bash
ffmpeg -y -loop 1 -framerate 1 \
  -i "/path/to/nanobanana_hero.jpg" \
  -i "/path/to/narrative_audio.mp3" \
  -c:v libx264 -tune stillimage -preset fast -crf 18 -threads 2 \
  -c:a aac -b:a 192k -pix_fmt yuv420p \
  -vf "scale=1280:960:force_original_aspect_ratio=decrease,pad=1280:960:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -shortest "~/Videos/{Canonical_Title}.mp4"
```

### Parameter Breakdown
- `-loop 1`: Loops the input image indefinitely until the shortest stream terminates.
- `-c:v libx264 -tune stillimage`: Compresses static frames with minimal CPU usage and maximum visual fidelity.
- `-vf "scale=...:decrease,pad=...":` Preserves original image aspect ratio without distortion, adding clean letterbox/pillarbox padding if needed.
  - **4:3 Aspect (Nanobanana Portraits & Plates):** `1280x960`
  - **16:9 Aspect (Widescreen / Landscapes):** `1920x1080`
  - **1:1 Aspect (Square / Cover Art):** `1080x1080`
  - **9:16 Aspect (Shorts / Reels / Vertical):** `1080x1920`
- `-c:a aac -b:a 192k`: High-fidelity stereo audio encoding.
- `-shortest`: Ends video immediately when the narrative audio stream terminates.

---

## 2. Multi-Plate Slideshow Video Generation (Dynamic Concat)

When multiple Nanobanana story plates exist for a narrative (e.g., 4 sequential monograph plates):

1. **Calculate Slide Duration**:
   $$\text{Slide Duration} = \frac{\text{Total Narrative Audio Duration}}{\text{Number of Image Plates}}$$
2. **Execute via the Bundled Helper Script**:
   Use the Python helper script [`render_av_video.py`](./scripts/render_av_video.py):
   ```bash
   python3 ./scripts/render_av_video.py \
     --images plate1.jpg plate2.jpg plate3.jpg plate4.jpg \
     --audio narrative_audio.mp3 \
     --output "~/Videos/Story - Nanobanana Monograph.mp4" \
     --aspect 4:3
   ```

---

## 3. Multiprocessing Batch Production Engine

To render multiple narrative videos concurrently from a JSON manifest without maxing out CPU cores:

```bash
python3 ./scripts/render_av_video.py \
  --batch ./examples/batch_manifest.example.json \
  --workers 2
```

See [`examples/batch_manifest.example.json`](./examples/batch_manifest.example.json) for the manifest schema:
```json
[
  {
    "title": "Historical Retrospective - Plate Series",
    "images": [
      "~/Pictures/plate_01.jpg",
      "~/Pictures/plate_02.jpg",
      "~/Pictures/plate_03.jpg"
    ],
    "audio": "~/Music/narrative_audio.mp3",
    "aspect": "4:3",
    "output": "~/Videos/Historical Retrospective.mp4"
  }
]
```

---

## 4. Universal Output Directory & Naming Invariants

- **Central Output Directory:** Defaults to `~/Videos/` (or platform equivalent, e.g., `%USERPROFILE%\Videos` on Windows).
- **Exact-Match Canonical Filename:** Use `{Canonical_Entity_Name} - {Site_Or_Brand_Suffix}.mp4`.
  - Example: `Purple Haze - Ganja House Strain Monograph.mp4`
  - Example: `Pra Somdej Prok Po - Ancient Amulet Monograph.mp4`
  - *Anti-Pattern:* Never use long SEO subtitles or keyword-stuffed strings in the video filename.

---

## 5. YouTube Syndication & Distribution Best Practices

- **Staging Review:** Default uploaded video privacy to `unlisted` for staging and editorial verification before public release.
- **Custom Thumbnails:** Attach the high-resolution Nanobanana hero image (4:3 or 16:9) directly as the custom video thumbnail.
- **Inbound Tracking:** Embed the canonical blog article or monograph permalink in the video description using tracking parameters (e.g. `?utm_source=youtube`).

---

## 6. YouTube Compliance & Anti-Strike Safeguards

To prevent automated policy flags and maximize algorithmic distribution:

1. **Upload Category:** Always specify Category `28` (Science & Technology) or `27` (Education).
2. **Zero Commercial Flags in Metadata:** Never include direct purchasing language ("buy", "order", "price", "$"), discount codes, or links to store checkout/cart URLs (`/shop/`, `/cart/`).
3. **Mandatory Educational Disclaimer Header:**
   ```text
   Educational & Botanical Documentary: An informational historical retrospective exploring the geographical origin, agricultural evolution, terpene chemistry, and cultural history of [Topic/Entity]. Produced exclusively for botanical, historical, and harm-reduction educational purposes.
   ```
4. **Outbound Linking:** Outbound links must point strictly to educational encyclopedic monographs or non-commercial reference resources.

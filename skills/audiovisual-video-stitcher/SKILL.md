---
name: audiovisual-video-stitcher
description: >-
  Universal audio-visual production suite for stitching podcast audio, monographs, and voice tracks
  with single featured images or multi-image slideshows into broadcast-grade MP4 video files.
  Includes FFmpeg still-image tuning, crossfade transition engines, and batch multiprocessing.
---

# Universal Audio-Visual & Slideshow MP4 Video Stitcher Skill

This skill provides complete operational recipes, FFmpeg configurations, and automated Python pipelines for turning audio podcasts, monographs, voice tracks, and spoken guides into high-definition `.mp4` video files for syndication, social channels, and YouTube broadcasting.

---

## 1. Single Still-Image Video Generation (Podcast Monograph)

When an audio podcast or voice monograph has a single featured/default hero image (e.g., a 4:3 art portrait or botanical strain photo):

### FFmpeg Command Recipe
```bash
ffmpeg -y -loop 1 -framerate 1 \
  -i "/path/to/featured_image.jpg" \
  -i "/path/to/podcast_audio.mp3" \
  -c:v libx264 -tune stillimage -preset fast -crf 18 -threads 2 \
  -c:a aac -b:a 192k -pix_fmt yuv420p \
  -vf "scale=1280:960:force_original_aspect_ratio=decrease,pad=1280:960:(ow-iw)/2:(oh-ih)/2,format=yuv420p" \
  -shortest "~/Videos/{Canonical_Title}.mp4"
```

### Parameter Breakdown
- `-loop 1`: Loops the input image indefinitely until the shortest stream terminates.
- `-c:v libx264 -tune stillimage`: Compresses static frames with minimal CPU and maximum visual fidelity.
- `-vf "scale=...:decrease,pad=...":` Preserves original image aspect ratio without distortion, adding clean letterbox/pillarbox padding if needed.
  - **4:3 Aspect (Portraits & Botanical Art):** `1280x960`
  - **16:9 Aspect (Widescreen / Landscapes):** `1920x1080`
  - **1:1 Aspect (Square / Cover Art):** `1080x1080`
  - **9:16 Aspect (Shorts / Reels / Vertical):** `1080x1920`
- `-c:a aac -b:a 192k`: High-fidelity stereo audio encoding.
- `-shortest`: Ends video immediately when audio terminates.

---

## 2. Multi-Image Slideshow Video Generation (Dynamic Concat)

When multiple body images or gallery photos exist for an article:

1. **Determine Slide Duration**:
   $$\text{Slide Duration} = \frac{\text{Total Audio Duration}}{\text{Number of Images}}$$
2. **Execute via the Bundled Helper Script**:
   Use the Python helper script [`render_av_video.py`](./scripts/render_av_video.py):
   ```bash
   python3 ./scripts/render_av_video.py \
     --images /path/to/img1.jpg /path/to/img2.jpg /path/to/img3.jpg \
     --audio /path/to/audio.mp3 \
     --output "~/Videos/Entity - Brand Monograph.mp4" \
     --aspect 4:3
   ```

---

## 3. Multiprocessing Batch Production Engine

To render multiple videos concurrently from a JSON manifest without maxing out CPU cores:

```bash
python3 ./scripts/render_av_video.py \
  --batch ./examples/batch_manifest.example.json \
  --workers 2
```

See [`examples/batch_manifest.example.json`](./examples/batch_manifest.example.json) for the manifest schema:
```json
[
  {
    "title": "Ancient Temple Bells - Episode 01",
    "images": [
      "~/Pictures/temple_entrance.jpg",
      "~/Pictures/bell_tower.jpg"
    ],
    "audio": "~/Music/episode_01.mp3",
    "aspect": "16:9",
    "output": "~/Videos/Ancient Temple Bells - Episode 01.mp4"
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
- **Custom Thumbnails:** Attach the high-resolution hero image (4:3 or 16:9) directly as the custom video thumbnail.
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

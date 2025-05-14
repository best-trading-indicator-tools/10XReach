# 10XReach - TikTok Video Processor

TikTok detects duplicates better than you think 

Here's how to beat the system 🧵

– File hash: every file has a digital fingerprint. If you upload the exact same file (no edits), TikTok can detect it instantly by comparing the hash.
– Visual/audio fingerprinting: TikTok uses AI to analyze frames and audio. Even if you cut 1 second or add text, it can still recognize the content.
– Metadata: things like creation date, device name, or codec can give clues. These are easy to change though, so they're not the main method.
– Audio matching: if your video uses a soundtrack or voice already on the platform, TikTok can detect it through audio fingerprinting.

How to avoid detection (aka not get flagged as a duplicate):

– Slightly crop or zoom the frame (e.g. zoom to 103%)
– Add overlay text (even a single invisible or tiny word)
– Use filters or tweak color settings (contrast, saturation, etc.)
– Change playback speed just a bit (e.g. 0.95x or 1.05x)
– Add a small watermark or dot in a corner

– Shift the audio pitch up/down slightly
– Add background noise (ambient sounds, white noise, etc.)
– Use TikTok's voiceover feature for a few seconds
– Cut or offset the audio by 0.2s to break the pattern

– Re-export the video using CapCut, Premiere, etc.
– Edit the metadata using tools like HandBrake or InShot

To avoid detection: modify at least 2-3 layers (visual, audio, metadata). Don't just trim a second or flip the video, go deeper.

This repository contains a Python script (`video_processor.py`) designed to process video files (e.g., downloaded from platforms like Instagram or TikTok) to prepare them for re-uploading to these or other platforms. The primary goal is to make these videos technically unique, which can help reduce the risk of being flagged or "shadowbanned" for being simple re-uploads, regardless of the source or destination platform (e.g., Instagram to TikTok, TikTok to Instagram, TikTok to TikTok, Instagram to Instagram).

## How it Works & Features Implemented

The `video_processor.py` script uses FFmpeg (a powerful open-source multimedia framework) to perform a series of transformations on input video files:

1.  **Input Source**: Processes `.mp4` video files located in a `videos/` subfolder.
2.  **Specific File Processing**: Can process all `.mp4` files in the `videos/` folder or a single specified video file using the `-f` or `--file` command-line argument.
3.  **Output Destination**: Saves the processed videos into a `treated/` subfolder, prefixing each filename with `tt_`.
4.  **Output Folder Cleaning**: Automatically clears all contents of the `treated/` folder before each processing run to ensure a fresh set of output files.
5.  **Metadata Removal**: Strips all existing metadata (e.g., Exif data, original creation timestamps, software tags) from the input videos using the `-map_metadata -1` FFmpeg option. This helps remove traces of the video's origin.
6.  **Resizing & Aspect Ratio**:
    *   Resizes videos to a standard 1080x1920 resolution (9:16 vertical aspect ratio), which is optimal for TikTok.
    *   Uses a combination of `scale` and `pad` filters in FFmpeg to ensure the video fits these dimensions, adding black bars if the original aspect ratio doesn't match (without cropping content).
    *   Sets the Sample Aspect Ratio (SAR) to 1:1 for compatibility.
7.  **Video Trimming**: Trims videos to a maximum duration of 29 seconds (`-t 29`), adhering to common short-form video limits and further altering the file from its original.
8.  **Visual Adjustments**:
    *   Applies a very slight brightness and contrast adjustment (`eq=brightness=0.005:contrast=1.005`) to subtly change the video's visual data.
    *   Performs a subtle 3 % centre-zoom (crop) to shift pixel positions enough to change TikTok's visual hash while remaining imperceptible to viewers.
    *   Adds a virtually invisible 2 × 2 px white dot in the top-left corner of every frame to further alter the bitmap without affecting user experience.
9.  **Video Encoding**:
    *   Uses the `libx264` codec for video encoding, which is widely compatible.
    *   Sets an explicit video bitrate of `6000k` (`-b:v 6000k`) to ensure consistent quality and a different video stream signature than a default transcode.
10. **Audio Re-encoding & Manipulation**:
    *   Re-encodes the audio stream to the AAC (Advanced Audio Coding) codec (`-c:a aac`).
    *   Sets an audio bitrate of `192k` (`-b:a 192k`) for good quality stereo audio.
    *   Applies a slight pitch shift (~3 %) via `asetrate`/`aresample` to alter the audio fingerprint without changing tempo.
    *   Offsets the audio track by 200 ms (`adelay`) to further break direct alignment with original material.
    *   **Optional Background Noise**: Can mix an external audio file as very low-volume background noise using the `--noise_file` argument. This adds another layer of audio uniqueness. The noise audio is looped and its volume is significantly reduced.
11. **Cross-Platform Compatibility**: The script is designed to be compatible with both macOS and Windows, provided Python 3 and FFmpeg are correctly installed and accessible. It includes logic to try and find the FFmpeg executable.

## Why These Steps Are Useful

Social media platforms like TikTok use algorithms to detect and sometimes deprioritize content that appears to be a direct, unaltered re-upload from other platforms or sources. By systematically modifying various technical aspects of the video, this script helps to:

*   **Create a Unique File Signature**: Changing metadata, resolution, bitrate, encoding parameters for both video and audio, duration, and optionally adding subtle background noise results in a file that is technically different from the original.
*   **Reduce Automated Detection**: These alterations can make it less likely for automated systems to flag the video as a simple duplicate.
*   **Optimize for TikTok**: Resizing to the preferred 9:16 aspect ratio ensures the video looks good on the platform.

While no script can guarantee that a video won't be subject to platform algorithms, these steps significantly enhance the "uniqueness" of the video file itself, which is a good practice when repurposing content.

## How to Use

1.  **Prerequisites**:
    *   **Python 3**: Ensure Python 3 is installed on your system.
    *   **FFmpeg**: Ensure FFmpeg is installed and accessible in your system's PATH, or the script will attempt to guide you if it can't find it in common locations.
2.  **Setup**:
    *   Place the `.mp4` video files you want to process into a folder named `videos/` in the same directory as the `video_processor.py` script.
3.  **Running the Script**:
    *   Open your terminal or command prompt.
    *   Navigate to the directory where `video_processor.py` is located.
    *   To process all videos in the `videos/` folder:
        ```bash
        python3 video_processor.py
        ```
    *   To process a specific video file (e.g., `my_video.mp4`) located in the `videos/` folder:
        ```bash
        python3 video_processor.py -f my_video.mp4
        ```
    *   To process a specific video and mix in background noise from `sounds/background_noise.mp3`:
        ```bash
        python3 video_processor.py -f my_video.mp4 --noise_file sounds/background_noise.mp3
        ```
    *   To process all videos and mix in background noise:
        ```bash
        python3 video_processor.py --noise_file sounds/background_noise.mp3
        ```
4.  **Output**:
    *   The processed videos will be saved in a folder named `treated/`, with each filename prefixed by `tt_`.

## Development So Far

This script was developed iteratively, adding features based on common requirements for video processing, particularly for social media:
*   Initial version focused on basic metadata removal, resizing, and trimming.
*   Enhanced to include slight visual adjustments (brightness/contrast) and explicit video bitrate.
*   Further improved by adding audio re-encoding instead of just copying the audio stream.
*   Made more user-friendly by adding command-line options for single-file processing and auto-clearing of the output directory.
*   Added optional background noise mixing for further audio differentiation.
*   Addressed and fixed bugs, such as an initial gray screen issue caused by a previous speed adjustment filter (which has since been removed). 
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

This repository contains a Python script (`video_processor.py`) and a Streamlit-based Graphical User Interface (`video_gui.py`) designed to process video files (e.g., downloaded from platforms like Instagram or TikTok) to prepare them for re-uploading to these or other platforms. The primary goal is to make these videos technically unique, which can help reduce the risk of being flagged or "shadowbanned" for being simple re-uploads, regardless of the source or destination platform (e.g., Instagram to TikTok, TikTok to Instagram, TikTok to TikTok, Instagram to Instagram).

The `video_processor.py` script handles the core FFmpeg processing, while `video_gui.py` provides an easy-to-use interface for it.

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
    *   **Horizontal Flip (Optional)**: Can horizontally flip the video using the `--hflip` command-line argument. This is another common technique to make content appear different to detection algorithms.
9.  **Video Encoding**:
    *   Uses the `libx264` codec for video encoding, which is widely compatible.
    *   Sets an explicit video bitrate of `6000k` (`-b:v 6000k`) to ensure consistent quality and a different video stream signature than a default transcode.
10. **Audio Re-encoding & Manipulation**:
    *   Re-encodes the audio stream to the AAC (Advanced Audio Coding) codec (`-c:a aac`).
    *   Sets an audio bitrate of `192k` (`-b:a 192k`) for good quality stereo audio.
    *   Applies a slight pitch shift (~3 %) via `asetrate`/`aresample` to alter the audio fingerprint without changing tempo.
    *   Offsets the audio track by 200 ms (`adelay`) to further break direct alignment with original material.
    *   **Automatic Background Noise**: If a file named `background_noise.mp3` exists in the `sounds/` directory, it is automatically mixed in as very low-volume background noise. This adds another layer of audio uniqueness. The noise audio is looped and its volume is significantly reduced. If the file is not found, the script automatically generates a low-volume white noise track that serves the same purpose, ensuring all videos have this audio uniqueness feature applied.
11. **Cross-Platform Compatibility**: The script is designed to be compatible with both macOS and Windows, provided Python 3 and FFmpeg are correctly installed and accessible. It includes logic to try and find the FFmpeg executable.
12. **Graphical User Interface (GUI)**: A `video_gui.py` script using Streamlit provides a user-friendly way to interact with the video processor. Features include:
    *   Drag-and-drop uploading of up to 10 `.mp4` video files at a time (default was 5, updated to 10 as per current GUI code).
    *   A global checkbox to enable/disable horizontal video flipping for all processed videos in a batch.
    *   **Per-Video Text Overlay Customization**: For each uploaded video, you can individually:
        *   Enable or disable text overlay.
        *   Set the text content.
        *   Choose text position (Top Center, Middle Center, Bottom Center).
        *   Define font size.
        *   Specify text color.
        *   Set a background color for the text (can be semi-transparent or "none").
        *   Choose text style: **Bold** and/or **Italic**. (Requires providing Roboto static font files in the `fonts/Roboto/static/` directory for reliable styling; see Font Handling section).
    *   Progress bar during processing.
    *   Download a `.zip` file containing all processed videos.

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
    *   **Dependencies**: Install required Python packages:
        ```bash
        pip install -r requirements.txt
        ```
    *   **Optional Background Noise File**: To enable custom background noise mixing, create a `sounds/` directory in the same location as the script, and place an audio file named `background_noise.mp3` inside it. If no custom noise file is provided, the script will automatically generate a subtle white noise track.
2.  **Setup**:
    *   Place the `.mp4` video files you want to process into a folder named `videos/` in the same directory as the `video_processor.py` script (this is mainly for the command-line version, the GUI uses direct uploads).
3.  **Running the Application**:

    There are two ways to use the video processor:

    **A) Using the Graphical User Interface (Recommended for ease of use):**
    *   Open your terminal or command prompt.
    *   Navigate to the project directory.
    *   **Font Handling for Text Overlays (Important!):** For best results with text overlays, especially for **Bold** and **Italic** styles using the default Roboto font, ensure you have the following static `.ttf` (TrueType Font) files in the `fonts/Roboto/static/` subfolder of your project:
        *   `Roboto-Regular.ttf` (for regular text)
        *   `Roboto-Bold.ttf` (for bold text)
        *   `Roboto-Italic.ttf` (for italic text)
        *   `Roboto-BoldItalic.ttf` (for bold and italic text)
        These files should be obtained from a font provider like Google Fonts (download the "static" versions, not variable fonts for this purpose). If these specific files are not found, the script will attempt to use system default fonts (like Helvetica on macOS or Arial on Windows), which may not support all styles or look as intended. The script will provide warnings in the console if it cannot find the requested styled Roboto fonts.
    *   Run the GUI:
        ```bash
        python3 -m streamlit run video_gui.py
        ```
        (If `python3` is not found, try `python -m streamlit run video_gui.py`)
    *   The GUI will open in your web browser. Drag and drop your videos, select options, and click "Process Videos".
    *   After processing, a download button will appear to get a `.zip` file of the treated videos.

    **B) Using the Command-Line Script (`video_processor.py`):**
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
    *   To process a specific video and flip it horizontally:
        ```bash
        python3 video_processor.py -f my_video.mp4 --hflip
        ```
    *   To process all videos and flip them horizontally:
        ```bash
        python3 video_processor.py --hflip
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
*   Added optional background noise mixing (automatically detected from `sounds/background_noise.mp3`) for further audio differentiation.
*   Addressed and fixed bugs, such as an initial gray screen issue caused by a previous speed adjustment filter (which has since been removed).
*   **Added a Streamlit-based GUI (`video_gui.py`)**:
    *   Allows drag-and-drop of up to 10 video files (updated from 5).
    *   Provides an option for horizontal flipping.
    *   **Introduced per-video customizable text overlays**:
        *   Toggle overlay on/off per video.
        *   Set custom text, position, font size, color, and background color.
        *   Options for **Bold** and **Italic** text styles (reliant on user-provided font files for best results).
    *   Displays processing progress.
    *   Enables downloading processed files as a `.zip` archive.

## Interpreting the SSIM Score (GUI)

When you process videos via `video_gui.py` a **SSIM** (%) column appears for each file:

* **SSIM (Structural Similarity Index)** compares every frame of the original input against the processed output, then averages the results.
* The GUI rescales both videos to 1080 × 1920 first, so we always compare like-for-like frames.
* The value is reported as a **percentage**:
  * **≈ 100 %**  → virtually identical (barely altered).
  * **90 – 95 %**  → minor visual changes only.
  * **80 – 90 %**  → moderate changes (good starting point, but might still be recognised on very popular clips).
  * **< 80 %**    → significant visual difference (lowest chance of duplicate-content flags).

### What score should I aim for?
TikTok's exact thresholds are unknown, but anecdotal evidence suggests:

* **≥ 95 %**: Too high – platform likely treats it as the same clip.
* **≈ 80–90 %**: Usually acceptable, yet if you want maximum safety add an extra tweak (e.g., overlay text, horizontal flip, stronger crop).
* **< 80 %**: Safe zone for most duplicate-detection systems.

Remember that TikTok also fingerprints **audio** and **metadata**. The script already tweaks those layers (pitch-shift, background noise, metadata wipe), so even an 80 % visual SSIM can be fine in practice.

> **In short:** An 80 % SSIM means the processed video still shares 80 % of its pixel structure with the source – it's changed by about 20 %. That is generally OK, but lower scores provide a wider safety margin. 
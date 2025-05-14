# 10XReach - TikTok Video Processor

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
10. **Audio Re-encoding**:
    *   Re-encodes the audio stream to the AAC (Advanced Audio Coding) codec (`-c:a aac`).
    *   Sets an audio bitrate of `192k` (`-b:a 192k`) for good quality stereo audio. This makes the audio stream technically different from the original.
    *   Applies a slight pitch shift (~3 %) via `asetrate`/`aresample`, so the audio fingerprint no longer matches the source while leaving the tempo intact.
    *   Offsets the audio track by 200 ms (`adelay`) to further break direct alignment with original material.
11. **Cross-Platform Compatibility**: The script is designed to be compatible with both macOS and Windows, provided Python 3 and FFmpeg are correctly installed and accessible. It includes logic to try and find the FFmpeg executable.

## Why These Steps Are Useful

Social media platforms like TikTok use algorithms to detect and sometimes deprioritize content that appears to be a direct, unaltered re-upload from other platforms or sources. By systematically modifying various technical aspects of the video, this script helps to:

*   **Create a Unique File Signature**: Changing metadata, resolution, bitrate, encoding parameters for both video and audio, and duration results in a file that is technically different from the original.
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
4.  **Output**:
    *   The processed videos will be saved in a folder named `treated/`, with each filename prefixed by `tt_`.

## Development So Far

This script was developed iteratively, adding features based on common requirements for video processing, particularly for social media:
*   Initial version focused on basic metadata removal, resizing, and trimming.
*   Enhanced to include slight visual adjustments (brightness/contrast) and explicit video bitrate.
*   Further improved by adding audio re-encoding instead of just copying the audio stream.
*   Made more user-friendly by adding command-line options for single-file processing and auto-clearing of the output directory.
*   Addressed and fixed bugs, such as an initial gray screen issue caused by a previous speed adjustment filter (which has since been removed). 
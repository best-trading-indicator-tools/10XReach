import os
import subprocess
import platform
import shutil # Added for rmtree
import argparse # Added for command-line arguments

# Potential font paths - adjust as needed or ensure font.ttf is in the project root
FONT_FILE_PATH_MACOS_SYSTEM = "/System/Library/Fonts/Helvetica.ttc"
FONT_FILE_PATH_WINDOWS_SYSTEM = "C:/Windows/Fonts/arial.ttf"
FONT_FILE_PROJECT_ROOT = "font.ttf"
FONT_FILE_BOLD = "font-bold.ttf"
FONT_FILE_ITALIC = "font-italic.ttf"
FONT_FILE_BOLD_ITALIC = "font-bolditalic.ttf"

def get_ffmpeg_path():
    """Detects FFmpeg path based on OS or prompts user if not found."""
    if platform.system() == "Windows":
        # Common locations for FFmpeg on Windows
        possible_paths = [
            "ffmpeg",  # If in PATH
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            os.path.expanduser("~\\ffmpeg\\bin\\ffmpeg.exe")
        ]
    else: # macOS or Linux
        possible_paths = [
            "ffmpeg", # If in PATH
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg", # Apple Silicon Homebrew
            os.path.expanduser("~/bin/ffmpeg")
        ]

    for path in possible_paths:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True)
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # If FFmpeg not found in common paths, try the default command "ffmpeg"
    print("FFmpeg not found in common paths. Attempting to use 'ffmpeg' from system PATH.")
    return "ffmpeg"

def get_font_path(is_bold=False, is_italic=False):
    """Attempts to find a suitable font file based on style."""
    font_to_try = []
    specific_style_found = False

    if is_bold and is_italic:
        font_to_try.append(FONT_FILE_BOLD_ITALIC)
    elif is_bold:
        font_to_try.append(FONT_FILE_BOLD)
    elif is_italic:
        font_to_try.append(FONT_FILE_ITALIC)
    
    # Check for specifically styled fonts first
    for f_style in font_to_try:
        if os.path.isfile(f_style):
            # print(f"Using styled font: {f_style}") # For debugging
            return f_style

    # Fallback to regular project font
    if os.path.isfile(FONT_FILE_PROJECT_ROOT):
        if font_to_try: # If a style was requested but not found
            print(f"Warning: Styled font for bold={is_bold}, italic={is_italic} not found (e.g., {font_to_try[0]}). Falling back to {FONT_FILE_PROJECT_ROOT}.")
        return FONT_FILE_PROJECT_ROOT

    # Fallback to system fonts
    system_font = None
    if platform.system() == "Darwin": # macOS
        if os.path.isfile(FONT_FILE_PATH_MACOS_SYSTEM):
            system_font = FONT_FILE_PATH_MACOS_SYSTEM
    elif platform.system() == "Windows":
        if os.path.isfile(FONT_FILE_PATH_WINDOWS_SYSTEM):
            system_font = FONT_FILE_PATH_WINDOWS_SYSTEM
    
    if system_font:
        if font_to_try: # If a style was requested but not found, and project font.ttf also not found
            print(f"Warning: Styled font (e.g., {font_to_try[0]}) and {FONT_FILE_PROJECT_ROOT} not found. Falling back to system font: {system_font}.")
        elif not os.path.isfile(FONT_FILE_PROJECT_ROOT):
             print(f"Warning: {FONT_FILE_PROJECT_ROOT} not found. Falling back to system font: {system_font}.")
        return system_font

    print(f"Warning: No specific or common font files found (tried: {', '.join(font_to_try) if font_to_try else 'none'}, {FONT_FILE_PROJECT_ROOT}, system defaults).")
    print("Drawtext filter might use a basic FFmpeg default font or fail if none is found by FFmpeg.")
    print(f"For best results and styling, place appropriate .ttf files (e.g., {FONT_FILE_PROJECT_ROOT}, {FONT_FILE_BOLD}, {FONT_FILE_ITALIC}) in your project directory.")
    return None # Let FFmpeg try to find a default

def _execute_ffmpeg_command(ffmpeg_executable, input_path, output_path, filename_for_log, noise_audio_path=None, horizontal_flip=False,
                            text_to_overlay=None, text_position=None, font_size=None, 
                            text_color=None, text_bg_color=None,
                            text_bold=False, text_italic=False):
    """Helper function to construct and run the FFmpeg command for a single file."""
    command = [
        ffmpeg_executable,
        "-i", input_path,
    ]

    if noise_audio_path:
        command.extend(["-stream_loop", "-1", "-i", noise_audio_path])

    # Base video filters
    vf_options = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,crop=iw*0.97:ih*0.97:(iw - iw*0.97)/2:(ih - ih*0.97)/2,drawbox=x=2:y=2:w=2:h=2:color=white@0.9:t=fill"
    
    if horizontal_flip:
        vf_options += ",hflip"
        
    vf_options += ",setsar=1,eq=brightness=0.005:contrast=1.005"

    # Add drawtext filter if text_to_overlay is provided
    if text_to_overlay and font_size and text_color:
        font_file = get_font_path(is_bold=text_bold, is_italic=text_italic)
        
        # Sanitize text for FFmpeg filter: escape single quotes and some special characters
        # This is a basic sanitization, more complex text might need more robust escaping
        sanitized_text = text_to_overlay.replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")

        drawtext_filter = f"drawtext=text='{sanitized_text}':fontcolor={text_color}:fontsize={font_size}"
        
        if font_file:
            # FFmpeg on Windows sometimes has issues with full paths in filter strings if they contain colons (e.g. C:)
            # Escaping the font file path is important, especially for Windows.
            escaped_font_file = font_file.replace("\\", "/").replace(":", "\\:") if platform.system() == "Windows" else font_file
            drawtext_filter += f":fontfile='{escaped_font_file}'"

        # Positioning
        if text_position == "Top Center":
            drawtext_filter += ":x=(w-text_w)/2:y=20" # 20px from top
        elif text_position == "Middle Center":
            drawtext_filter += ":x=(w-text_w)/2:y=(h-text_h)/2"
        elif text_position == "Bottom Center":
            drawtext_filter += ":x=(w-text_w)/2:y=h-th-20" # 20px from bottom
        else: # Default to Bottom Center if somehow unspecified
            drawtext_filter += ":x=(w-text_w)/2:y=h-th-20"

        # Background box for text
        if text_bg_color and text_bg_color.lower() != "none" and text_bg_color.lower() != "transparent":
            drawtext_filter += f":box=1:boxcolor={text_bg_color}:boxborderw=10" # 10px padding for the box
        
        vf_options += f",{drawtext_filter}"

    command.extend([
        "-map_metadata", "-1",
        "-vf", vf_options, # Use the constructed vf_options string
        "-t", "29", # Trim output to 29 seconds
        "-c:v", "libx264",
        "-b:v", "6000k",
    ])

    if noise_audio_path:
        # [0:a] is main video's audio, [1:a] is noise audio
        # Process main audio: pitch shift and delay
        # Process noise audio: set volume very low
        # Mix them. duration=first ensures output lasts as long as the (trimmed) main video.
        filter_complex_str = (
            "[0:a]aresample=48000,asetrate=48000*1.03,aresample=48000,adelay=200|200[main_processed];"
            "[1:a]volume=0.02[noise_quiet];"
            "[main_processed][noise_quiet]amix=inputs=2:duration=first[audio_out]"
        )
        command.extend([
            "-filter_complex", filter_complex_str,
            "-map", "0:v",      # Map video from the first input
            "-map", "[audio_out]", # Map audio from the filter_complex output
        ])
    else:
        # Original audio processing if no noise file
        command.extend([
            "-filter:a", "aresample=48000,asetrate=48000*1.03,aresample=48000,adelay=200|200",
        ])

    command.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-y",
        output_path
    ])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully processed '{filename_for_log}' -> '{os.path.basename(output_path)}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing '{filename_for_log}':")
        print(f"FFmpeg command: {' '.join(e.cmd)}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: FFmpeg executable not found at '{ffmpeg_executable}'.")
        print("Please ensure FFmpeg is installed and the path is correct.")
        # This error is critical, so we might want to indicate a halt
        raise # Re-raise to be caught by the main processing loop if needed

def process_videos(input_folder, output_folder, ffmpeg_executable, specific_filename=None, noise_audio_path=None, horizontal_flip=False):
    """
    Processes videos in the input folder and saves them to the output folder.
    If specific_filename is provided, only that file (within input_folder) is processed.
    If noise_audio_path is provided, it will be mixed into the output.
    If horizontal_flip is True, the video will be flipped horizontally.
    """
    files_to_process = []
    if specific_filename:
        if not specific_filename.lower().endswith(".mp4"):
            print(f"Error: Specified file '{specific_filename}' is not an .mp4 file. Skipping.")
            return 0, 1 # (processed_count, skipped_count)
        
        # Construct full path to check existence
        full_input_path = os.path.join(input_folder, specific_filename)
        if not os.path.isfile(full_input_path):
            print(f"Error: Specified file '{specific_filename}' not found in '{input_folder}'. Skipping.")
            return 0, 1
        files_to_process.append(specific_filename)
    else:
        for f_name in os.listdir(input_folder):
            if f_name.lower().endswith(".mp4"):
                files_to_process.append(f_name)

    if not files_to_process:
        if specific_filename:
            # This case is already handled by the checks above, but as a safeguard:
            print(f"No file to process (specific file: {specific_filename}).")
        else:
            print(f"No .mp4 files found in '{input_folder}'.")
        return 0, 0

    processed_count = 0
    skipped_count = 0

    for filename in files_to_process:
        input_path = os.path.join(input_folder, filename)
        output_filename = f"tt_{filename}"
        output_path = os.path.join(output_folder, output_filename)

        print(f"Processing '{filename}'...")
        if noise_audio_path:
            print(f"Mixing with background noise: {noise_audio_path}")
        try:
            if _execute_ffmpeg_command(ffmpeg_executable, input_path, output_path, filename, noise_audio_path=noise_audio_path, horizontal_flip=horizontal_flip):
                processed_count += 1
            else:
                skipped_count += 1
        except FileNotFoundError: # Raised by _execute_ffmpeg_command if ffmpeg path is bad
            print("Halting processing due to FFmpeg not being found.")
            # Return current counts, as further processing is not possible
            return processed_count, skipped_count + (len(files_to_process) - processed_count - skipped_count)
        except Exception as e:
            print(f"An unexpected error occurred while processing {filename}: {e}")
            skipped_count +=1
            
    return processed_count, skipped_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process videos for TikTok. Removes metadata, resizes, trims, and optionally adjusts visuals and audio.")
    parser.add_argument("-f", "--file", type=str, help="Filename of a specific video to process (must be in the input folder). Processes all .mp4 files if not specified.")
    parser.add_argument("--hflip", action="store_true", help="Horizontally flip the video.")
    args = parser.parse_args()

    input_video_folder = "videos"
    output_video_folder = "treated"

    # Auto-clear output folder contents
    if os.path.exists(output_video_folder):
        print(f"Clearing contents of output folder: {output_video_folder}")
        for item_name in os.listdir(output_video_folder):
            item_path = os.path.join(output_video_folder, item_name)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f'Failed to delete {item_path}. Reason: {e}')
    else:
        os.makedirs(output_video_folder)
        print(f"Created output folder: {output_video_folder}")

    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path: # Should be caught by get_ffmpeg_path itself, but as a safeguard
        print("Could not determine FFmpeg path. Exiting.")
        exit(1)
    
    print(f"Using FFmpeg from: {ffmpeg_path}")

    # Check if input folder exists, especially if processing all files
    if not args.file and not os.path.isdir(input_video_folder):
        print(f"Error: Input folder '{input_video_folder}' not found.")
        print(f"Please create it and place your .mp4 videos inside, or specify a single file with --file.")
        exit(1)
    elif args.file and not os.path.isdir(input_video_folder):
        # This might be okay if the file path is absolute, but our design implies it's relative to input_video_folder
        print(f"Warning: Input folder '{input_video_folder}' not found, but a specific file was requested. Assuming it's accessible.")
        # The check for specific file existence is now inside process_videos

    # Determine if default background noise file exists
    default_noise_path = "sounds/background_noise.mp3"
    actual_noise_path = None
    if os.path.isfile(default_noise_path):
        actual_noise_path = default_noise_path
        print(f"Default background noise file found: {actual_noise_path}. It will be used.")
    else:
        print(f"Default background noise file not found at '{default_noise_path}'. Proceeding without background noise.")

    processed_count, skipped_count = process_videos(input_video_folder, output_video_folder, ffmpeg_path, specific_filename=args.file, noise_audio_path=actual_noise_path, horizontal_flip=args.hflip)

    print(f"\nProcessing complete.")
    print(f"Successfully processed: {processed_count} files.")
    print(f"Skipped/Failed: {skipped_count} files.")
    if skipped_count > 0:
        print("Check the console output above for error details on failed files.")
    print(f"Cleaned videos are in: {output_video_folder}") 
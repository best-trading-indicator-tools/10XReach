import os
import subprocess
import platform
import shutil # Added for rmtree
import argparse # Added for command-line arguments
import re  # Added for SSIM parsing
import math # For converting degrees to radians
import random  # For randomised zoom/pan

# Potential font paths - adjust as needed or ensure font.ttf is in the project root
FONT_FILE_PATH_MACOS_SYSTEM = "/System/Library/Fonts/Helvetica.ttc"
FONT_FILE_PATH_WINDOWS_SYSTEM = "C:/Windows/Fonts/arial.ttf"
# Updated font paths to target specific Roboto static files
FONT_DIR = "fonts/Roboto/static/"
FONT_FILE_REGULAR = os.path.join(FONT_DIR, "Roboto-Regular.ttf")
FONT_FILE_BOLD = os.path.join(FONT_DIR, "Roboto-Bold.ttf")
FONT_FILE_ITALIC = os.path.join(FONT_DIR, "Roboto-Italic.ttf")
FONT_FILE_BOLD_ITALIC = os.path.join(FONT_DIR, "Roboto-BoldItalic.ttf")

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
    font_to_use = None
    style_description = "regular"

    if is_bold and is_italic:
        style_description = "bold italic"
        if os.path.isfile(FONT_FILE_BOLD_ITALIC):
            font_to_use = FONT_FILE_BOLD_ITALIC
    elif is_bold:
        style_description = "bold"
        if os.path.isfile(FONT_FILE_BOLD):
            font_to_use = FONT_FILE_BOLD
    elif is_italic:
        style_description = "italic"
        if os.path.isfile(FONT_FILE_ITALIC):
            font_to_use = FONT_FILE_ITALIC

    if font_to_use: # Specific styled font found
        # print(f"Using styled font: {font_to_use}") # For debugging
        return font_to_use
    
    # Fallback to regular Roboto if styled version wasn't found or not requested
    if os.path.isfile(FONT_FILE_REGULAR):
        if style_description != "regular":
            print(f"Warning: Roboto {style_description} font ({FONT_FILE_BOLD_ITALIC if style_description == 'bold italic' else (FONT_FILE_BOLD if style_description == 'bold' else FONT_FILE_ITALIC)}) not found in '{FONT_DIR}'. Falling back to {FONT_FILE_REGULAR}.")
        return FONT_FILE_REGULAR

    # Fallback to system fonts if no Roboto fonts are found
    system_font = None
    if platform.system() == "Darwin": # macOS
        if os.path.isfile(FONT_FILE_PATH_MACOS_SYSTEM):
            system_font = FONT_FILE_PATH_MACOS_SYSTEM
    elif platform.system() == "Windows":
        if os.path.isfile(FONT_FILE_PATH_WINDOWS_SYSTEM):
            system_font = FONT_FILE_PATH_WINDOWS_SYSTEM
    
    if system_font:
        print(f"Warning: Roboto fonts not found in '{FONT_DIR}'. Falling back to system font: {system_font}.")
        return system_font

    print(f"Warning: No Roboto or common system font files found. Searched in '{FONT_DIR}'.")
    print("Drawtext filter might use a basic FFmpeg default font or fail if none is found by FFmpeg.")
    print(f"Please ensure Roboto font files (e.g., {FONT_FILE_REGULAR}, {FONT_FILE_BOLD}, etc.) are in '{FONT_DIR}'.")
    return None # Let FFmpeg try to find a default

def _execute_ffmpeg_command(ffmpeg_executable, input_path, output_path, filename_for_log, noise_audio_path=None, horizontal_flip=False,
                            text_to_overlay=None, text_position=None, font_size=None, 
                            text_color=None, text_bg_color=None,
                            text_bold=False, text_italic=False,
                            rotation_degrees=0.0,
                            playback_speed=1.0,
                            random_zoom_pan=False,
                            apply_film_grain=False,
                            zoom_end_scale=None):
    """Helper function to construct and run the FFmpeg command for a single file."""
    command = [
        ffmpeg_executable,
        "-i", input_path,
    ]

    if noise_audio_path:
        command.extend(["-stream_loop", "-1", "-i", noise_audio_path])

    # Base video filters
    vf_options_list = [
        "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    ]

    # Mild CRF compression (random 21–25) instead of fixed bitrate
    crf_val = random.randint(21, 25)

    # Ken Burns / Zoom-pan.

    # Priority: if a specific zoom_end_scale (>1.0) is supplied (e.g., via GUI slider), honour it.
    # Otherwise fall back to the old behaviour controlled by random_zoom_pan boolean flag.

    if zoom_end_scale and zoom_end_scale > 1.0001:
        # Use the provided zoom_end_scale, but still randomise the pan path for variety
        zoom_end = min(max(1.01, zoom_end_scale), 2.00)  # Clamp sensibly
        zoom_increment = (zoom_end - 1.0) / (29 * 30)  # per-frame increment (~30 fps, 29 s)

        # Random pan offsets up to ±30 % of the available area so we avoid static centre crop
        pan_offset_x = random.choice([-1, 1]) * random.uniform(0.0, 0.3)
        pan_offset_y = random.choice([-1, 1]) * random.uniform(0.0, 0.3)

        x_expr = f"(iw/2-(iw/zoom/2))+{pan_offset_x:.4f}*(iw - iw/zoom)"
        y_expr = f"(ih/2-(ih/zoom/2))+{pan_offset_y:.4f}*(ih - ih/zoom)"

        vf_options_list.append(
            f"zoompan=z='min(max(1,zoom)+{zoom_increment:.6f},{zoom_end:.2f})':x='{x_expr}':y='{y_expr}':s=1080x1920:d=1:fps=30"
        )

    elif random_zoom_pan:
        # Random final zoom between 1.12 and 1.18 (≈12–18 %)
        zoom_end = random.uniform(1.12, 2.00)
        zoom_increment = (zoom_end - 1.0) / (29 * 30)  # per-frame increment assuming 30 fps

        # Random pan offsets: up to ±30 % of available pan range along each axis
        pan_offset_x = random.choice([-1, 1]) * random.uniform(0.0, 0.3)
        pan_offset_y = random.choice([-1, 1]) * random.uniform(0.0, 0.3)

        x_expr = f"(iw/2-(iw/zoom/2))+{pan_offset_x:.4f}*(iw - iw/zoom)"
        y_expr = f"(ih/2-(ih/zoom/2))+{pan_offset_y:.4f}*(ih - ih/zoom)"

        vf_options_list.append(
            f"zoompan=z='min(max(1,zoom)+{zoom_increment:.6f},{zoom_end:.2f})':x='{x_expr}':y='{y_expr}':s=1080x1920:d=1:fps=30"
        )
    else:
        # Default subtle Ken Burns from 1.0 × → 1.1 ×
        zoom_increment = (1.1 - 1.0) / (29 * 30)
        vf_options_list.append(
            f"zoompan=z='min(max(1,zoom)+{zoom_increment:.6f},1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:d=1:fps=30"
        )
    
    # Add rotation if specified
    if rotation_degrees != 0.0:
        rotation_radians = math.radians(rotation_degrees)
        # bilinear=0 (nearest neighbor) is faster but lower quality for large rotations.
        # Consider 'bicubic' for better quality if needed, though slower.
        # fillcolor=black ensures empty areas from rotation are black.
        vf_options_list.append(f"rotate={rotation_radians:.6f}:bilinear=0:fillcolor=black")
    
    vf_options_list.append("drawbox=x=2:y=2:w=2:h=2:color=white@0.9:t=fill")
    
    if horizontal_flip:
        vf_options_list.append("hflip")
        
    # Pixel-aspect and basic colour tweak
    vf_options_list.append("setsar=1")
    vf_options_list.append("eq=brightness=0.005:contrast=1.005")

    # Automatic subtle hue shift (±5°). The user doesn't need to set anything.
    hue_shift_deg = random.uniform(-5.0, 5.0)
    vf_options_list.append(f"hue=h={hue_shift_deg:.2f}*PI/180:s=1")

    # Automatic light film-grain noise (random strength 4–8) to further lower SSIM
    grain_strength = random.randint(4, 8)
    vf_options_list.append(f"noise=alls={grain_strength}:allf=t")

    # Automatic subtle lens distortion (barrel/pincushion). Random k1=k2 in 0.008–0.02
    k_val = round(random.uniform(0.008, 0.02), 4)
    vf_options_list.append(f"lenscorrection=k1={k_val}:k2={k_val}")

    # Apply playback speed adjustment via setpts (avoid grey-frame using STARTPTS)
    if abs(playback_speed - 1.0) > 0.001:
        vf_options_list.append(f"setpts=(PTS-STARTPTS)/{playback_speed}")

    vf_options = ",".join(vf_options_list)

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
        "-crf", str(crf_val),
    ])

    # Build audio filter
    if noise_audio_path:
        # [0:a] is main video's audio, [1:a] is noise audio
        # Process main audio: pitch shift and delay
        # Process noise audio: set volume very low
        # Mix them. duration=first ensures output lasts as long as the (trimmed) main video.
        # Append atempo for playback speed if needed (valid 0.5-2.0 for our 0.9-1.1 range)
        speed_audio_chain = f",atempo={playback_speed}" if abs(playback_speed - 1.0) > 0.001 else ""
        filter_complex_str = (
            "[0:a]aresample=48000,asetrate=48000*1.03,aresample=48000,adelay=200|200" + speed_audio_chain + "[main_processed];"
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
        audio_chain = "aresample=48000,asetrate=48000*1.03,aresample=48000,adelay=200|200"
        if abs(playback_speed - 1.0) > 0.001:
            audio_chain += f",atempo={playback_speed}"
        command.extend([
            "-filter:a", audio_chain,
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

def compute_ssim_percent(ffmpeg_executable, original_path, processed_path):
    """Returns average SSIM between two videos as a percentage (0–100). Returns None if unavailable."""
    cmd = [
        ffmpeg_executable,
        "-i", original_path,
        "-i", processed_path,
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v0];" +
        "[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v1];" +
        "[v0][v1]ssim",
        "-f", "null", "-"
    ]
    try:
        # Run FFmpeg, don't check exit code as ssim with -f null - often exits non-zero.
        # Capture stderr as that's where ssim stats are.
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60) # Added timeout
    except subprocess.TimeoutExpired:
        print(f"SSIM calculation timed out for {os.path.basename(original_path)} vs {os.path.basename(processed_path)}")
        return None
    except Exception as e:
        print(f"Error running FFmpeg for SSIM calculation: {e}")
        return None

    # Try to find a line like: "[Parsed_ssim_0 @ ...] SSIM Y:0.123 U:0.456 V:0.789 All:0.321 (...)"
    # We are interested in the "All:0.321" part.
    # The regex looks for "SSIM", then any characters non-greedily (.*?), then "All:", then captures the number.
    match = re.search(r"SSIM.*?All:\s*([0-9\.]+)", result.stderr)

    if match:
        try:
            ssim_float = float(match.group(1))
            return ssim_float * 100.0  # Convert to percentage
        except ValueError:
            print(f"Could not convert SSIM value '{match.group(1)}' to float.")
            # Print the full stderr if conversion fails, as the regex matched something
            print(f"Full FFmpeg stderr for {os.path.basename(original_path)} on conversion error:\n{result.stderr}")
            return None
    else:
        print(f"SSIM 'All:' pattern not found in FFmpeg stderr for {os.path.basename(original_path)}.")
        # Print the full stderr if no regex match
        print(f"Full FFmpeg stderr for {os.path.basename(original_path)} on pattern not found:\n{result.stderr}")
        return None

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
        # Generate white noise using FFmpeg if no file exists
        temp_noise_path = os.path.join(output_video_folder, "temp_noise.mp3")
        try:
            # Create 30 seconds of white noise (already at low volume)
            noise_cmd = [
                ffmpeg_path,
                "-f", "lavfi",
                "-i", "anoisesrc=amplitude=0.05:color=white:duration=30",
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                "-y",
                temp_noise_path
            ]
            subprocess.run(noise_cmd, check=True, capture_output=True)
            actual_noise_path = temp_noise_path
            print(f"No background noise file found. Generated low-volume white noise.")
        except Exception as e:
            print(f"Failed to generate white noise: {e}")
            print("Proceeding without background noise.")

    processed_count, skipped_count = process_videos(input_video_folder, output_video_folder, ffmpeg_path, specific_filename=args.file, noise_audio_path=actual_noise_path, horizontal_flip=args.hflip)

    print(f"\nProcessing complete.")
    print(f"Successfully processed: {processed_count} files.")
    print(f"Skipped/Failed: {skipped_count} files.")
    if skipped_count > 0:
        print("Check the console output above for error details on failed files.")
    print(f"Cleaned videos are in: {output_video_folder}")
    
    # Clean up temporary noise file if it was created
    temp_noise_path = os.path.join(output_video_folder, "temp_noise.mp3")
    if os.path.exists(temp_noise_path):
        try:
            os.remove(temp_noise_path)
            print("Temporary noise file removed.")
        except Exception as e:
            print(f"Failed to remove temporary noise file: {e}") 
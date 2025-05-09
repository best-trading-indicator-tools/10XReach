import os
import subprocess
import platform
import shutil # Added for rmtree
import argparse # Added for command-line arguments

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


def _execute_ffmpeg_command(ffmpeg_executable, input_path, output_path, filename_for_log):
    """Helper function to construct and run the FFmpeg command for a single file."""
    # FFmpeg command construction (as previously defined)
    # -vf: scale, pad, setsar, eq (brightness/contrast)
    # -t 29: Trim
    # -c:v libx264, -b:v 6000k: Video codec and bitrate
    # -c:a aac -b:a 192k: Audio re-encode to AAC at 192kbps
    # -map_metadata -1: Remove metadata
    # -y: Overwrite output
    command = [
        ffmpeg_executable,
        "-i", input_path,
        "-map_metadata", "-1",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,eq=brightness=0.005:contrast=1.005",
        "-t", "29",
        "-c:v", "libx264",
        "-b:v", "6000k",
        "-c:a", "aac",
        "-b:a", "192k",
        "-y",
        output_path
    ]

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

def process_videos(input_folder, output_folder, ffmpeg_executable, specific_filename=None):
    """
    Processes videos in the input folder and saves them to the output folder.
    If specific_filename is provided, only that file (within input_folder) is processed.
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
        try:
            if _execute_ffmpeg_command(ffmpeg_executable, input_path, output_path, filename):
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
    parser = argparse.ArgumentParser(description="Process videos for TikTok. Removes metadata, resizes, trims, and optionally adjusts visuals.")
    parser.add_argument("-f", "--file", type=str, help="Filename of a specific video to process (must be in the input folder). Processes all .mp4 files if not specified.")
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

    processed_count, skipped_count = process_videos(input_video_folder, output_video_folder, ffmpeg_path, specific_filename=args.file)

    print(f"\nProcessing complete.")
    print(f"Successfully processed: {processed_count} files.")
    print(f"Skipped/Failed: {skipped_count} files.")
    if skipped_count > 0:
        print("Check the console output above for error details on failed files.")
    print(f"Cleaned videos are in: {output_video_folder}") 
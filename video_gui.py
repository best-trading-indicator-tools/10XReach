import os
import tempfile
import shutil
import streamlit as st
import zipfile
import io # Import io for BytesIO

from video_processor import get_ffmpeg_path, _execute_ffmpeg_command

st.set_page_config(page_title="10XReach Video Processor", page_icon="🎞️", layout="centered")

st.title("🎞️ 10XReach Video Processor GUI")

# Upload section
uploaded_files = st.file_uploader(
    label="Drag & drop up to 10 .mp4 videos (or click to browse)",
    type=["mp4"],
    accept_multiple_files=True,
)

horizontal_flip = st.checkbox("Horizontally flip video (same as --hflip)")

process_btn = st.button("Process Videos")

if process_btn:
    # Basic validations
    if not uploaded_files:
        st.warning("Please upload at least one .mp4 file.")
        st.stop()
    if len(uploaded_files) > 10:
        st.error("You can process a maximum of 10 videos at a time.")
        st.stop()

    # Prepare output directory
    output_dir = "treated"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Detect optional background noise
    noise_path = None
    default_noise = os.path.join("sounds", "background_noise.mp3")
    if os.path.isfile(default_noise):
        noise_path = default_noise

    # Get FFmpeg path
    ffmpeg_path = get_ffmpeg_path()

    # Temp directory to hold uploaded files during processing
    with tempfile.TemporaryDirectory() as tmpdir:
        progress = st.progress(0)
        success_count, fail_count = 0, 0

        for idx, file in enumerate(uploaded_files, start=1):
            filename = file.name
            tmp_input_path = os.path.join(tmpdir, filename)
            with open(tmp_input_path, "wb") as f:
                f.write(file.getbuffer())

            output_path = os.path.join(output_dir, f"tt_{filename}")

            st.write(f"Processing {filename} ...")
            if _execute_ffmpeg_command(
                ffmpeg_path,
                tmp_input_path,
                output_path,
                filename,
                noise_audio_path=noise_path,
                horizontal_flip=horizontal_flip,
            ):
                success_count += 1
            else:
                fail_count += 1

            progress.progress(idx / len(uploaded_files))

    st.success(f"Processing complete. Successfully processed {success_count} file(s). Failed: {fail_count}.")
    st.info(f"Processed videos saved to the '{output_dir}' folder.")

    # Offer download if successful
    if success_count > 0:
        # Create a temporary file on disk to build the zip archive
        # This is better for potentially large zip files than keeping everything in memory initially
        temp_zip_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        temp_zip_path = temp_zip_file.name

        try:
            with zipfile.ZipFile(temp_zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(output_dir):
                    for file_in_zip in files: # Renamed variable to avoid conflict
                        full_path = os.path.join(root, file_in_zip)
                        zf.write(full_path, arcname=file_in_zip)
            
            # Close the file so its contents can be read reliably
            temp_zip_file.close()

            # Read the contents of the created zip file into memory for Streamlit
            with open(temp_zip_path, "rb") as f_read:
                zip_bytes = f_read.read()
            
            st.download_button(
                label="Download Processed Videos (.zip)",
                data=zip_bytes, # Pass the bytes
                file_name="processed_videos.zip",
                mime="application/zip"
            )
        finally:
            # Clean up the temporary zip file from disk
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path) 
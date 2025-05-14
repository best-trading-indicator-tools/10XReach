import os
import tempfile
import shutil
import streamlit as st
import zipfile
import io # Import io for BytesIO

from video_processor import get_ffmpeg_path, _execute_ffmpeg_command, compute_ssim_percent

st.set_page_config(page_title="10XReach Video Processor", page_icon="🎞️", layout="centered")

st.title("🎞️ 10XReach Video Processor GUI")

# Make drag-and-drop zone taller/more prominent
st.markdown(
    """
    <style>
    /* Target the main file uploader container */
    div[data-testid="stFileUploader"] {
        border: 3px dashed rgba(0, 128, 0, 0.5) !important; /* Green dashed border for visibility */
        padding: 30px !important; /* Increased padding for the main container */
        background-color: rgba(240, 240, 240, 0.5) !important; /* Light grey background for main container */
        border-radius: 20px !important; /* Increased border-radius */
    }

    /* Target the actual dropzone section within the file uploader */
    div[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {
        min-height: 900px !important; /* Make the actual drop area even taller */
        background-color: rgba(220, 220, 255, 0.5) !important; /* Light blue background for dropzone */
        border: 2px solid rgba(0, 0, 255, 0.3) !important; /* Blue solid border for dropzone */
        border-radius: 15px !important; /* Increased border-radius */
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 60px !important; /* Increased padding inside the dropzone */
        box-sizing: border-box !important;
    }

    /* Style the instruction text within the dropzone */
    div[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] [data-testid="stFileUploadDropzoneInstructions"],
    div[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] button { /* Also style the button text if it exists */
        font-size: 1.3em !important; /* Slightly larger text */
        font-weight: bold !important;
        color: #333 !important;
    }

    /* Style the main label of the file uploader if needed */
    div[data-testid="stFileUploader"] label[data-testid="stWidgetLabel"] {
        font-size: 1.15em !important; /* Slightly larger label */
        font-weight: bold !important;
        margin-bottom: 15px !important; /* Increased margin */
        display: block !important; /* Ensure it takes its own line */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Upload section
uploaded_files = st.file_uploader(
    label="Drag & drop up to 10 .mp4 videos (or click to browse)",
    type=["mp4"],
    accept_multiple_files=True,
)

# --- Processing Options ---
st.subheader("Processing Options")
horizontal_flip = st.checkbox("Horizontally flip video (same as --hflip)")

# ----------------------------
# Per-video text overlay settings
# ----------------------------
if uploaded_files:
    st.markdown("### Text Overlay Settings (per video)")
    for idx, file in enumerate(uploaded_files):
        with st.expander(f"Text settings for: {file.name}", expanded=True):
            st.checkbox("Add text overlay", key=f"add_text_{idx}")
            if st.session_state.get(f"add_text_{idx}"):
                st.text_input("Text to display", key=f"text_{idx}", value="Your Text Here")
                st.selectbox(
                    "Text position",
                    ("Top Center", "Middle Center", "Bottom Center"),
                    index=2,
                    key=f"pos_{idx}"
                )
                st.number_input("Font size", min_value=10, max_value=200, value=24, key=f"size_{idx}")
                st.text_input("Text color (e.g., white, #FF0000)", value="white", key=f"color_{idx}")
                st.text_input("Background color (e.g., black@0.5, none)", value="black@0.5", key=f"bg_{idx}")
                # Font style options
                col1, col2 = st.columns(2)
                with col1:
                    st.checkbox("Bold", key=f"bold_{idx}")
                with col2:
                    st.checkbox("Italic", key=f"italic_{idx}")

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

            # Retrieve overlay settings for this file
            add_text = st.session_state.get(f"add_text_{idx-1}", False)
            text_to_overlay = st.session_state.get(f"text_{idx-1}") if add_text else None
            text_position = st.session_state.get(f"pos_{idx-1}") if add_text else None
            font_size = st.session_state.get(f"size_{idx-1}") if add_text else None
            text_color = st.session_state.get(f"color_{idx-1}") if add_text else None
            text_bg_color = st.session_state.get(f"bg_{idx-1}") if add_text else None
            text_bold = st.session_state.get(f"bold_{idx-1}", False) if add_text else False
            text_italic = st.session_state.get(f"italic_{idx-1}", False) if add_text else False

            st.write(f"Processing {filename} ...")
            # Execute FFmpeg for processing
            processed_ok = _execute_ffmpeg_command(
                ffmpeg_path,
                tmp_input_path,
                output_path,
                filename,
                noise_audio_path=noise_path,
                horizontal_flip=horizontal_flip,
                text_to_overlay=text_to_overlay,
                text_position=text_position,
                font_size=font_size,
                text_color=text_color,
                text_bg_color=text_bg_color,
                text_bold=text_bold,
                text_italic=text_italic
            )

            # Compute SSIM similarity percentage if processing succeeded
            ssim_percent = None
            if processed_ok:
                success_count += 1
                ssim_percent = compute_ssim_percent(ffmpeg_path, tmp_input_path, output_path)
                print(f"DEBUG SSIM for {filename}: {ssim_percent}") # Debug print for console
            else:
                fail_count += 1

            # Display result row with similarity score
            result_cols = st.columns([4, 1])
            with result_cols[0]:
                status_icon = "✅" if processed_ok else "❌"
                st.write(f"{status_icon} {filename}")
            with result_cols[1]:
                if ssim_percent is not None:
                    st.metric(
                        label="SSIM",
                        value=f"{ssim_percent:.2f}%",
                        help=(
                            "SSIM (Structural Similarity Index) measures visual similarity between the original "
                            "and processed video on a scale of 0–100. We scale both videos to 1080×1920 and "
                            "compute frame-by-frame SSIM, then average the values. Higher scores mean the output "
                            "looks almost identical to the source; lower scores indicate larger visual changes. "
                            "Seeing different scores for clips processed with the same FFmpeg settings is normal "
                            "because each source clip starts with different resolution, quality, and content. "
                            "The metric helps gauge how much the video has been altered—useful to ensure the "
                            "repurposed video is sufficiently different to avoid TikTok duplicate-content flags."
                        )
                    )
                else:
                    st.write("N/A")

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
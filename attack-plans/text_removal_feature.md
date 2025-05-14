# Attack Plan: Text Removal from Videos

## 1. Goal
Implement a feature to optionally detect and remove existing text from video frames. This would help in making repurposed content more unique by removing prior watermarks, captions, or other embedded text.

## 2. Challenges
*   **Text Detection Accuracy:** Reliably identifying text across various fonts, sizes, colors, languages, orientations, and complex backgrounds in video frames.
*   **Inpainting Quality:** After text removal, seamlessly filling the vacated region with a background that is consistent with the surrounding area, avoiding noticeable artifacts or blurs. This is especially hard with dynamic or textured backgrounds.
*   **Computational Cost & Performance:** Text detection and inpainting are computationally intensive. Processing every frame of a video can be very time-consuming and resource-heavy, potentially making the script too slow for practical use without significant optimization or powerful hardware.
*   **Complexity of Integration:** This is beyond FFmpeg's native capabilities and will require integrating external computer vision libraries and potentially machine learning models.
*   **Variability in Text:** Text can be static (like a watermark) or dynamic (like burnt-in subtitles). It can be opaque or semi-transparent.

## 3. Potential Approaches & Technologies

### A. OpenCV-based Solution (Python)
*   **Text Detection:**
    *   **EAST (Efficient and Accurate Scene Text Detector):** A deep learning model known for good performance in detecting text in natural scenes. OpenCV has an implementation.
    *   **CRAFT (Character Region Awareness for Text Detection):** Another strong contender, often providing precise character-level bounding boxes.
    *   **OCR Engines (e.g., Tesseract via `pytesseract`):** Can detect text, but might be slower and less robust for varied in-video text compared to dedicated scene text detectors. Primarily designed for document OCR.
*   **Inpainting:**
    *   **OpenCV `cv2.inpaint()`:** Offers methods like `INPAINT_NS` (Navier-Stokes based) and `INPAINT_TELEA`. These are faster but can produce blurry results on complex backgrounds.
    *   **PatchMatch:** A content-aware fill algorithm. Implementations might be available or could be adapted.
    *   **Generative Inpainting (Advanced):** Using GANs (Generative Adversarial Networks) or other deep learning models trained for inpainting. This offers the highest quality but is the most complex and resource-intensive. Libraries like `lama-cleaner` or similar research projects could be explored.

### B. Cloud-based Vision APIs
*   **Services:** Google Cloud Vision API, AWS Rekognition, Azure Computer Vision.
*   **Pros:**
    *   Often provide powerful, pre-trained models for text detection (OCR).
    *   Managed infrastructure, potentially less local setup.
*   **Cons:**
    *   **Cost:** API calls can be expensive, especially for video processing (many frames).
    *   **Latency:** Sending frames to the cloud and back adds overhead.
    *   **Limited Inpainting:** Most cloud OCR services focus on *reading* text, not necessarily *removing and inpainting* it seamlessly. Object removal features might exist but may not be fine-tuned for text.
    *   **Internet Dependency.**

### C. Specialized Libraries/Pre-trained Models
*   Search for open-source projects or pre-trained models specifically focused on "text removal from images/videos" or "video object removal."
*   Examples (conceptual, specific libraries need research):
    *   Libraries built on top of PyTorch or TensorFlow that package detection and inpainting.

## 4. Proposed Integration Plan (High-Level)

1.  **New Module:** Create a new Python module (e.g., `text_remover.py`).
2.  **Core Function:** This module would have a function like `remove_text_from_frame(frame_image, detection_confidence_threshold)` which takes a single video frame (as a NumPy array, for instance, via OpenCV) and returns the processed frame.
3.  **Video Processing Loop:**
    *   In `video_processor.py`, when text removal is enabled for a video:
        *   Decode the video frame by frame (e.g., using OpenCV's `VideoCapture`).
        *   For each frame, pass it to `text_remover.remove_text_from_frame()`.
        *   Re-encode the processed frames into a new video (e.g., using OpenCV's `VideoWriter` or by piping frames back to FFmpeg). This re-encoding step needs careful handling to preserve audio and other desired output settings.
4.  **GUI Option:**
    *   In `video_gui.py`, add a checkbox for each uploaded video: "Attempt to remove existing text."
    *   Pass this option to the `process_videos` function and subsequently to the per-file processing logic.
5.  **Dependencies:** Add new dependencies (e.g., `opencv-python`, `pytesseract`, potentially deep learning frameworks if using advanced models) to `requirements.txt`.

## 5. Phased Implementation & Proof of Concept (PoC)

*   **Phase 1: Research & Tool Selection (Still Images)**
    *   Evaluate different text detection models (EAST, CRAFT) on a diverse set of sample images with text.
    *   Evaluate different inpainting techniques (OpenCV basic, PatchMatch, simple deep learning if feasible) on the same images after manually masking text regions.
    *   **Deliverable:** Decision on the best-performing combination for a PoC, focusing on a balance of quality and complexity.
*   **Phase 2: PoC for Single Image Text Removal**
    *   Develop a Python script that takes an image path, applies the chosen detection and inpainting methods, and saves the output.
    *   **Deliverable:** Working PoC script for still images.
*   **Phase 3: Video Integration PoC**
    *   Adapt the PoC to process a short video clip.
    *   Address frame-by-frame processing, and re-assembly into a video.
    *   Initial performance assessment.
    *   **Deliverable:** Basic video text removal PoC.
*   **Phase 4: Integration into Main Application**
    *   Refine the video processing pipeline.
    *   Integrate into `video_processor.py` and `video_gui.py` with the toggle option.
    *   Manage dependencies.
    *   Optimize performance where possible (e.g., frame skipping if applicable, batch processing if models support it, efficient re-encoding).
*   **Phase 5: Testing & Refinement**
    *   Test with a wide variety of videos.
    *   Gather feedback on quality and speed.
    *   Iterate on model parameters or techniques if needed.

## 6. Considerations & Open Questions
*   **Performance:** This is the biggest concern. How slow will it be? Will users wait?
*   **Quality:** How good will the inpainting be? Will artifacts be acceptable?
*   **Error Handling:** What if text isn't detected, or inpainting fails badly?
*   **Resource Usage:** Will it require significant CPU/GPU/RAM?
*   **Configurability:** Will users need to tune detection thresholds or choose inpainting methods? (Initially, aim for sensible defaults).
*   **Alternatives:** Is there a simpler FFmpeg filter or a very lightweight tool that could do a "good enough" job for *some* types of text (e.g., solid color watermarks)? (Likely not for general text, but worth a quick re-check).

This plan provides a starting point for a complex feature. Each phase, especially research and PoC, will reveal more about feasibility and the best path forward. 
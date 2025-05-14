# Attack Plan: Pushing SSIM Below 60 %

## 1. Goal
Lower the average SSIM between the original and processed videos from the current ~70 % plateau to **< 60 % (ideally 50–55 %)** while maintaining perceptual quality suitable for TikTok.

## 2. Key Observations
* Current pipeline already applies:
  * 3 % centre-zoom (Ken Burns from 1.00 → 1.10 over 29 s).
  * ±0–2 ° optional rotation.
  * Minor brightness (+0.5 %) and contrast (+0.5 %) tweaks.
  * 2 × 2 px white dot overlay.
* Despite these, SSIM rarely drops below 70 %. The biggest contributors to similarity are large unchanged pixel areas plus static colour histograms.

## 3. Variables With Highest Leverage
Below are the adjustable parameters ranked by expected **SSIM impact ↗** vs **perceived quality ↘** (lower is better for quality loss):

| # | Variable / FFmpeg filter | Current | Proposed Range | SSIM impact | Quality cost |
|---|--------------------------|---------|----------------|-------------|--------------|
| 1 | `zoompan` final zoom     | 1.10    | 1.12 – 1.18    | ★★★★☆       | ★★☆☆☆ |
| 2 | `zoompan` X/Y pan path   | Fixed centre | Randomised ease-in/out pan (top→mid, left→right etc.) | ★★★★☆ | ★★☆☆☆ |
| 3 | `rotate` degrees         | 0 – 2    | ±0.5 – 1.0     | ★★★☆☆ | ★☆☆☆☆ |
| 4 | `hue` shift (degrees)    | 0        | ±3 – 8         | ★★★☆☆ | ★★☆☆☆ |
| 5 | `eq` brightness/contrast | +0.5 %   | ±2 – 3 %       | ★★★☆☆ | ★★☆☆☆ |
| 6 | `noise` (grain)          | none     | `alls=8:allf=t` | ★★★☆☆ | ★☆☆☆☆ |
| 7 | Compression level (`-crf` / `-b:v`) | fixed 6000 k | allow CRF-based target (e.g. CRF 23) | ★★☆☆☆ | ★★☆☆☆ |
| 8 | Perspective / `lenscorrection` | none | `lenscorrection=k1=0.02:k2=0.02` | ★★☆☆☆ | ★★☆☆☆ |

## 4. Recommended Parameter Changes (MVP)
1. **Increase and randomise zoom:**  
   Replace constant 1 → 1.10 with `zoompan=z='min(max(1,zoom)+0.00025,1.15)'` (≈ 15 % end-zoom). Introduce X/Y pan path tied to zoom so cropping area moves slightly (e.g. start top-left → end centre).
2. **Keep rotation subtle:** Limit GUI slider to –1 ° … +1 ° (smaller default 0.7 °). Even ~0.8 ° combined with other tweaks lowers SSIM ~5 pts without noticeable tilt.
3. **Colour hue shift:** Add optional `hue=h=2*random(0)*PI/180:s=1` for ±2–3 ° hue change (barely perceptible to eye).
4. **Add film-grain style noise:** `noise=alls=6:allf=t` (slightly gentler than previous).
5. **Expose "Uniqueness strength" knob:** Single scalar 0 – 100 that linearly scales above variables so user can trade quality vs. uniqueness.

## 5. Stretch Ideas
* **Temporal jitter:** Drop or duplicate 1 – 2 % of frames (`minterpolate`, `tblend`) to disrupt frame-level SSIM.
* **Subtle lens distortion:** `lenscorrection=k1=0.02:k2=0.02` creates slight barrel distortion, hard to notice on phones.
* **Per-frame random grain mask:** Procedurally generate 2-frame-periodic random noise so consecutive frames differ more.

## 6. Implementation Roadmap
1. **Parameterisation layer** (video_processor.py)
   * Add `uniqueness_strength` (0–100). Map to:
     * zoom final = 1.10 + 0.0005 × strength  (cap 1.18)
     * rotation default = ±0.5 ° + 0.04 × strength (cap 5 °)
     * hue shift = ±0 ° + 0.06 × strength (cap 8 °)
     * noise alls = 0 + 0.08 × strength (cap 10)
2. **GUI slider** in `video_gui.py` to expose this single setting instead of multiple independent toggles.
3. **FFmpeg filter updates:**
   * Construct dynamic `zoompan`, `rotate`, `hue`, and `noise` strings based on the mapped values.
4. **A/B test:** Process 10 sample videos at strengths 25/50/75 and log SSIM to verify sub-60 % is reached without obvious degradation.
5. **Polish & ship:** Tune default (strength = 40) to hit ~55 % SSIM on average.

## 7. Risks & Mitigations
* **Perceived quality drop:** Keep colour & noise subtle (< 8 % hue shift; noise < 10) and preview in GUI.
* **Processing load:** Additional filters add ~10 % CPU; acceptable. Use `bilinear` for rotation to keep cost low.
* **Edge artefacts from zoom/pan:** Ensure `pad` stays 1080×1920 and `fillcolor=black` to mask borders.

## 8. Success Criteria
* ≥ 80 % of test videos produce **SSIM ≤ 60 %** at default strength.
* No user complaints about obvious visual degradation after 50+ real-world uploads.
* Pipeline runtime increases by **< 15 %** compared with current default settings. 
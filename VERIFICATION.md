# Source verification

Date: 2026-11-06. Scope: public-safe source, original dynamic camera/effects and licensed short-sample demonstrations.

## Environment

Linux, Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, Pillow 13.0.0, FFmpeg 7.1.5 with libx264 and AAC. Noto Sans CJK Bold Traditional Chinese face 3 and DejaVu Sans Condensed Bold resolve through fontconfig. Dependency versions are recorded in requirements-lock.txt. Other platforms and a fresh network-isolated dependency installation have not been tested.

## Checks

- All top-level modules compile. Fresh-process imports leave market data uninitialized; only explicit initialization or a CLI loads observations.
- 34 unit tests pass. They cover CSV validation, explicit input, deterministic effects/audio, timeline boundaries, full-story short-input rejection, camera range and zoom changes, unmodified observations, partial-week extrema, protected information panels, configurable watermark, label and frame-time validation, repeat initialization, unknown first-session daily change (N/A / 未提供前收 rather than zero), and exact deterministic ZIP membership/hashes.
- The fixed narrative now requires exactly 1999-01-05 through 2026-11-06. Full-story initialization and 11 representative frames are tested with an explicitly artificial in-memory fixture containing cited event closes solely to exercise validation. This is not an accurate historical film or visual acceptance using actual full-history data. No artificial fixture CSV or rendered frames are bundled.
- The 2026-11-06 closing event cites TWSE dated reports and a CNA article. The closing fact was independently rechecked against the public TWSE report and CNA. Factual verification is not a data redistribution license.
- Dynamic public smoke render: `python dynamic_film.py --demo --seconds 3 --fps 6`. FFprobe: 3.000 seconds, 18 H.264 frames, 720 × 1280, AAC stereo, 44.1 kHz. A 2.4-second public-demo still was inspected for Traditional Chinese glyphs, observed date/price, short-sample warning, source attribution, original chart effects and the requested 紀順文X小狐AI watermark.
- The original three-day preview also passes a 3-second, 6-fps smoke render with the watermark.
- CLI without explicit input rejects the request; the three-day sample is rejected for the full story. The explicit `--demo` path uses only the licensed bundled public sample.
- The source ZIP is built twice with identical SHA-256; CRC, exact allowlist and each member's SHA-256 are verified. Only 29 explicitly named files are bundled, including SHA256SUMS. Movies, WAVs, images, logs, credentials, private manifests and private time series are excluded.

## Limits

- No full 232-second historical render or end-to-end visual acceptance was performed for this revision. The public demo contains only three sessions and cannot reproduce that story.
- Original dynamic camera/effects were adapted to explicit initialization and public-safe inputs. The private revision's expanded audio arrangement was not transplanted; the existing procedural score is retained. No subjective audio listening was performed.
- Camera planning smooths framing at 30 Hz and may anticipate future viewport ranges. Visible OHLC and dates remain discrete; current weekly candles include only reached sessions. Decorative lights, rings and particles are not market measurements.
- Layout is fixed at 720 × 1280. Full-story text and effects have only representative automated frame checks, not exhaustive overlap review. Changing fonts, dimensions or long captions requires visual review.
- Input validation checks daily density and cited events, not exchange-calendar completeness or legal rights. Data and footage publication rights remain the caller's responsibility.
- Fonts, FFmpeg and package binaries are not bundled. Encoded media is not promised byte-identical across versions/platforms. Source ZIP reproducibility assumes identical contents and Python/zlib behavior.

Checks used OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 as optional resource limits.

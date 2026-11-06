# TAIEX Cinematic

Original Python animation, visual effects and synthesized music for a vertical TAIEX history film. This is newly written project code, not the original project of any reference-video creator. No reference pixels, logos, music, assets or source code are included.

**The runnable public demo has only three actual sessions: 2026-11-02 through 2026-11-04. The 232-second, 1999–2026 cinematic story requires a separately obtained, authorized matching daily dataset. A clean checkout alone cannot reproduce that full historical film.**

## Quick start

Use Python 3.12. Install FFmpeg with the libx264 encoder and AAC support, Noto Sans CJK, DejaVu Sans, and fontconfig using your system's normal trusted package manager. These system tools and fonts are not bundled.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python preview.py
python dynamic_film.py --demo
```

The demo writes `output/three_day_preview.mp4`, a silent intermediate, an original synthesized WAV and QA JSON. The default is 12 seconds, 720 × 1280, 30 fps. It has no spoken narration. A fast smoke test is `python preview.py --seconds 3 --fps 6`; `--still` writes a PNG instead.

The layout is designed for 720 × 1280. Do not change canvas dimensions without adapting and checking the fixed layout coordinates. Red denotes rising values and green denotes falling values in the Taiwan market convention.

### Portable font configuration

With fontconfig, the configured family names resolve installed fonts. On another platform, explicitly set `TAIEX_CJK_FONT` and `TAIEX_LATIN_FONT` to your installed font files. Set `TAIEX_CJK_FACE_INDEX` to the Traditional Chinese face of your chosen TTC (default 3 for the tested Noto collection, usually 0 for a standalone font). No developer-machine font paths are required. Validate glyphs and licensing for replacement fonts.

## Dynamic camera and watermark

`python dynamic_film.py --demo --seconds 3 --fps 6` renders the same three official sessions with original camera pan/zoom, endpoint tracking, partial-week aggregation, orbital rings, particle streaks, beat lights and a fixed information panel. Decorative motion is not a market measurement. The default watermark is **紀順文X小狐AI**; change it with `--watermark "Your credit"` or omit it with `--watermark ""`. `--source-label "Your licensed source"` changes the on-screen attribution and QA metadata. Labels accept up to 64 characters without control characters. The original public preview also includes the default watermark.

For the full dynamic treatment, supply your own authorized daily data:

```sh
python dynamic_film.py --data YOUR_AUTHORIZED_DAILY_TAIEX.csv --source-label "Your licensed source" --output output/dynamic.mp4
python dynamic_film.py --demo --still 8 --output output/demo.png
```

No private footage, full-history dataset, third-party creator source, reference assets or sampled audio is bundled. The dynamic treatment uses the existing original procedural score, not the separate private revision's expanded audio arrangement. Source licensing does not grant market-data or rendered-footage redistribution rights.

The full narrative requires exactly 1999-01-05 through 2026-11-06. Camera values are eased at 30 Hz; visible dates and prices remain discrete observations. Framing uses offline smoothing that may anticipate future ranges, but never reveals future candles or interpolates market prices. Zoomed views switch between daily candles and weekly candles whose last bucket includes only sessions reached. This is a fixed 720 × 1280 layout, not a general responsive layout system. The short demo cannot validate historical storytelling or visually reproduce the full film.

## Your own observations

```sh
python render.py --data YOUR_AUTHORIZED.csv --output output/custom.mp4 --duration 12
python render.py --data YOUR_AUTHORIZED.csv --preview --output output/still.png
```

Alternatively set the `TAIEX_INPUT_CSV` environment variable. An explicit `--data` takes precedence. The renderer performs no data downloading, network requests or automatic fallback to a private file.

Required CSV columns: `date,close`. Optional: `open,high,low,ohlc_verified`. Dates use YYYY-MM-DD. Values must be positive and finite; dates must be unique. Rows are sorted by date. Only the exact Boolean text `true` permits candles; `false` or an absent verification column uses the observed closing-price line. Verified candles require coherent real OHLC. Missing observations are never fabricated or interpolated as market facts. Do not label synthetic or inferred OHLC as verified.

An optional generic `render.py --events events.json` accepts a JSON list with `start`, `end`, and `title` per item. The separately bundled historical milestone JSON is the fixed cinematic story's format, not this generic format.

## Full cinematic story

```sh
python high_fidelity_hook.py --data YOUR_AUTHORIZED_DAILY_TAIEX.csv --output output/hook.mp4
python long_film.py --data YOUR_AUTHORIZED_DAILY_TAIEX.csv --source-label "Your licensed data source" --output output/full.mp4
```

The full narrative covers exactly 1999-01-05 through 2026-11-06. It checks verified daily OHLC, broad annual row density, event dates and independently cited event closing values. Those checks **do not establish exchange-calendar completeness or data licensing**; both remain the caller's responsibility. Supplying sparse or wrong-period data fails instead of silently inventing history. The short hook also requires data beginning 1999-01-05 and covering at least 2001-09-28.

Use `--start 58 --seconds 58 --silent-only` for a silent section, or `--still 8` for a frame. Public sample files are deliberately insufficient for these commands. Opening peak/trough, decline, elapsed days, endpoint values, rankings and heatmaps derive from the supplied observations. The 1990 reference is an independently cited single intraday high, not invented pre-1999 OHLC.

Weekly/monthly candles aggregate only sessions already reached: first observed open, maximum high, minimum low and final observed close. The latest bucket may be partial. Camera easing and visual particles are interpolated; market observations are not. Annual rankings use 2000–2025 price-index year-end returns, exclude partial 1999 and 2026, and do not include dividends. Cited events describe context, not proof that a single event caused an entire price move.

The private preview used a third-party dataset restricted to private noncommercial use. That dataset and all its rendered derivatives are absent. The source license does not permit you to republish data or footage for which you lack rights. Set accurate source attribution and obey your data provider's terms before distributing a rendered film.

## Original music

`python score_long.py --seconds 12 --output output/music.wav` generates audio without market data or audio-file inputs. It uses oscillators and seeded noise, not sampled recordings. The full-film CLI passes event timing for impacts and chimes. Segment renders generate their own fade/normalization, so separately rendered audio excerpts are not guaranteed sample-identical to a crop of the full score. For final assembly render the full score once and trim it consistently.

## Contents and verification

- `render.py`: observed-price renderer and strict CSV loader.
- `high_fidelity_hook.py`, `long_film.py`: original cinematic treatments and fixed narrative.
- `camera_film.py`, `dynamic_film.py`, `branding.py`: explicit-initialization camera, dynamic effects, stable HUD and configurable watermark.
- `effects.py`, `timeline.py`, `runtime.py`: effects, discrete observation mapping, fonts, input and encoding.
- `score_long.py`: original procedural score.
- `preview.py`: runnable licensed three-day demo.
- `data/`: only two small government-open-data samples, provenance and cited public event facts.
- `tests/`: tests using public samples and explicitly artificial validation fixtures.
- `build_source_zip.py`: strict whitelist packaging; rendered output is never included.
- `VERIFICATION.md`: exact checks and limits for this release candidate.

The code is MIT. Data, fonts, FFmpeg and Python packages retain their own terms. See `THIRD_PARTY_NOTICES.md`, `LICENSE` and the retained Pillow wheel notice. No source or assets from A4UX, WanlinStudio, TESLA-STOCK-PRICE or Stock-Insight-AI are copied. 

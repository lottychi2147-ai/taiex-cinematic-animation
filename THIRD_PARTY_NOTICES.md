# Third-party and data notices

## Original code

The renderer, layout, visual effects and synthesized-score code were newly authored for this project, under the accompanying MIT license. No creator reference code/assets, logos, videos, screenshots, audio samples or melodies are bundled. MIT does not relicense dependencies, input data or reference works.

## Three-day official sample

`data/official_20261102_04.csv` and `data/official_open_data_latest.json` contain three TWSE observations, 2026-11-02 to 2026-11-04. Provider: Taiwan Stock Exchange (臺灣證券交易所). Dataset: Weighted Stock Price Index Historical Data.

- Catalog: https://data.gov.tw/dataset/11755
- API: https://openapi.twse.com.tw/v1/indicesReport/MI_5MINS_HIST
- Government Data Open License, version 1.0: https://data.gov.tw/license

Adaptations: ROC-to-Gregorian date normalization, numeric conversion and explicit OHLC verification flag. This is not a complete historical dataset.

## Eleven-session archived official sample

`data/official_archive_20261001_16.csv` contains 11 observations dated 2026-10-01 through 2026-10-16 from an archived copy of the same government-open-data dataset. It is a third-party preservation, not a current API response or the full month. Source and transformations are recorded in `data/october_provenance.json`.

Archive: https://github.com/dunay2/pec2-visualizacion-datos/blob/9b1c4e5d99fafc45350d5456cb704ee1bbd066ac/data/taiex.csv

Only this data sample is reused, not repository code. Data-specific attribution and Government Data Open License 1.0 apply.

## Public event facts

`data/verified_milestones.json` contains independently cited historical facts and original short narration, not a raw market-data series. Individual links identify news and official sources. No article bodies or screenshots are reproduced. An event's intraday high/low, closing value, annual percentage and event date are distinct and must not be interchanged. The 1990-02-12 reference 12,682.41 is a cited intraday high; no 1990–1998 OHLC is supplied or fabricated.

## Runtime dependencies, not bundled

- Python 3.12: Python Software Foundation licensing, https://docs.python.org/3/license.html
- NumPy 2.3.5: BSD-3-Clause, https://github.com/numpy/numpy
- pandas 2.2.3: BSD-3-Clause, https://github.com/pandas-dev/pandas
- Pillow 13.0.0: **MIT-CMU**, not standard MIT or HPND. https://github.com/python-pillow/Pillow . The installed distribution's complete license file, including bundled-library notices, is retained as `licenses/Pillow-13.0.0-LICENSE.txt`; no Pillow code or binaries are bundled.
- FFmpeg: the installed build and enabled components determine applicable LGPL/GPL and other terms. No executable is bundled. https://ffmpeg.org/legal.html
- Noto Sans CJK: SIL Open Font License 1.1, not bundled. https://github.com/notofonts/noto-cjk
- DejaVu Sans: upstream font license, not bundled. https://dejavu-fonts.github.io/License.html

## Explicitly excluded

The complete private-use market dataset and its derived monthly data, movies, WAVs, reference frames, screenshots, logs, private manifests, credentials, machine paths and account details are excluded. No full-history license is granted by this package. No code or assets from A4UX, 灣林Studio/WanlinStudio, TESLA-STOCK-PRICE or Stock-Insight-AI are included.

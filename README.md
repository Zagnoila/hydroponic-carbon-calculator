# Growprint

A single-page carbon footprint calculator for small hydroponic farms, built for AgTech by Ian Rosenthal.

Enter your farm's production, electricity, water, materials, travel and equipment. Python calculates the annual footprint, crop-cycle emissions, production and intensity metrics. The page updates in place with an interactive seven-category pie chart and an accessible breakdown table.

**Live website:** [ian-rosenthal-growprint.vercel.app](https://ian-rosenthal-growprint.vercel.app/)

## Run locally

Python 3.9 or newer is required. In a terminal, inside this project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5057**. On Windows, activate with `.venv\Scripts\activate` instead.

## Files

- `app.py`: Flask page route and JSON calculation endpoint.
- `calculator.py`: all carbon calculations, input validation, field definitions and source factors.
- `templates/index.html`: the one page containing the form and results.
- `static/style.css`: responsive layout, colors and typography.
- `static/script.js`: sends the form to Python, then displays returned numbers and draws the chart. It does not calculate emissions or percentages.
- `static/vendor/chart.umd.js`: locally served Chart.js 4.4.8, with its MIT license.
- `tests/test_calculator.py`: reference parity, all categories, validation, zero guards and endpoint tests.
- `build.py` and `vercel.json`: Python-capable deployment configuration. The build copies `static/` to `public/static/` for Vercel's CDN.

## Reference and method

The authoritative source is the assignment's [Hydroponic Carbon Footprint Calculator workbook](https://docs.google.com/spreadsheets/d/1tkGwkPDtqRkXlu5lfNHK5l_IliIhMGI2/edit). See [the cell-by-cell implementation map](reference/formula-map.md).

The six default factors are copied exactly: electricity **0.3497 kg CO₂e/kWh**, water **0.0015 kg CO₂e/gallon**, nutrients **2.5 kg CO₂e/kg**, growing media **1 kg CO₂e/kg**, packaging **2 kg CO₂e/kg**, and travel **0.4 kg CO₂e/mile**. Equipment's total embodied carbon is divided by its useful life.

The grid factor is the workbook's U.S. eGRID 2023 default, not a current or location-specific rate. Other defaults are illustrative screening values. Users can supply local or supplier-specific factors in the optional panel. No unrelated factors have been substituted.

The reference's example yields **506.79514 kg CO₂e/year**, **80 lb/year**, **50.679514 kg CO₂e/cycle**, **50.679514 kg CO₂e/sq ft/year**, and **6.33493925 kg CO₂e/lb**. Values are rounded only for display.

## Input behavior

- Blank activity fields count as zero; blank factor fields use the workbook defaults. Explicit zero factors stay zero.
- Negative numbers, non-finite numbers, invalid strings, runtimes over 24 hours/day and operating days over 366 are rejected. Numbers are capped at one billion to reject unreasonable or overflowing requests.
- Zero denominators return numeric zero in the API, matching the spreadsheet's `IF` formulas. The UI shows **N/A** for undefined intensity metrics and explains what is missing.
- If equipment carbon is positive but useful life is zero, equipment is excluded to match the workbook and the page displays an explicit warning.
- The area guidance is 2–20 sq ft. Other non-negative areas are calculated with an out-of-range note.
- Input changes mark prior results as stale. Calculate refreshes them. Reset clears all entered values and the result section.
- The app stores no farm entries. Requests are calculated in memory.

## Test

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

## Deploy

Import this repository into Vercel on its free Hobby plan and use the Flask framework. The included configuration builds the assets, and Vercel runs `app.py` as Python. For a conventional Python host, install `requirements.txt` and run `gunicorn app:app --bind 0.0.0.0:$PORT`.

The AgTech editor's browser sandbox cannot run Flask and blocks external network requests. The working deployment demonstrates the complete application; the editor receives the actual source files. No JavaScript replacement is used to imitate Python calculations.

## Credits and scope

Fonts: **DM Sans** and **Fraunces**, loaded through Google Fonts. Hydroponic illustration and interface are SVG/HTML/CSS. Chart: Chart.js, MIT license in `static/vendor/`.

This screening estimate includes purchased electricity and selected supply-chain emissions. It is not a formal life-cycle assessment. Building construction and employee commuting are excluded, following the reference workbook.

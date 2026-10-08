# LIBS: A Research Overview (Quarto / reveal.js)

Research seminar on laser-induced breakdown spectroscopy (LIBS) by Christian L. Goueguel, built with [Quarto](https://quarto.org) and reveal.js.

**View the slides:** https://christiangoueguel.com/libs-research-overview/

**Contents**

1. **Wavelength-selective excitation**: resonance-enhanced LIBS (RELIBS), resonant laser-ablation LIF (RLA-LIF) and laser-ablation LIF (LA-LIF) for trace analysis in alloys.
2. **Groundwater monitoring**: underwater LIBS of dissolved metals in CO₂-saturated solutions up to 400 bar.
3. **Estimating soil texture**: predicting sand, silt and clay from LIBS spectra with PLSR and elastic net (validation protocol, tuning, test-set performance, variable importance).

## Render & present

```bash
quarto render libs-research-overview.qmd
```

Open `libs-research-overview.html` in a browser. It is fully self-contained (figures and fonts embedded), so it works offline and can be emailed.

| Key | Action |
|-----|--------|
| `→` / `Space` | next slide / fragment |
| `S` | speaker view (every slide has speaker notes) |
| `F` | full screen |
| `M` or ☰ | slide menu |
| `Alt`+click | zoom into a figure |
| `Esc` | slide overview |

PDF: open the HTML in Chrome with `?print-pdf` appended to the URL, then Print → Save as PDF (landscape, no margins).
The elastic-net tuning surface (Part 3) is an interactive WebGL plot (drag to rotate, Sand/Silt/Clay buttons); it may not appear in a PDF export.

## Files

- `libs-research-overview.qmd`: the deck (title-slide kicker and `date` are set in this file)
- `assets/theme.scss`: theme (colors, typography, layouts, slide-entry animations)
- `assets/deck-scripts.html`: count-up animation for the headline numbers
- `assets/charts/_*.md`: generated SVG charts; regenerate with `python3 scripts/make_charts.py` (Parts 1–2, title) and `python3 scripts/make_soil_charts.py` (Part 3)
- `data/soil-texture/`: results extracted read-only from `Granulo_pls_enet.RData` (tuning results, CV resamples, test-set predictions, PLSR VIP, wavelength calibration)
- `scripts/extract_soil_results.R`: re-creates `data/soil-texture/` from the `.RData` (no model is re-trained; needs caret, pls, glmnet, jsonlite)
- `images/`: figures extracted from the original PDF at full resolution

"""Generate the inline-SVG charts used in libs-research-overview.qmd.

Run from the project root:  python3 scripts/make_charts.py
Each chart is written to assets/charts/_<name>.md as a raw-HTML block and
pulled into the deck with {{< include >}}. Data values are transcribed from the
original slides / publications; edit the DATA sections below to update them.
"""

from math import log10
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "charts"
OUT.mkdir(parents=True, exist_ok=True)


def write(name, svg):
    (OUT / f"_{name}.md").write_text("```{=html}\n" + svg.strip() + "\n```\n")


def f(v):
    return f"{v:.1f}"


# ---------------------------------------------------------------------------
# 1. Pb detection limits: LIBS vs RLA-LIF vs LA-LIF (log-scale dot plot)
# ---------------------------------------------------------------------------
PB = [  # (method, sub-label, DL in ppm)
    ("LIBS", "conventional single pulse", 200.0),
    ("RLA-LIF", "one tunable pulse · 1.4 J/cm²", 8.0),
    ("LA-LIF", "ablation + tunable excitation", 0.2),
]


def pb_chart():
    x0, dec = 330, 185  # x of 0.1 ppm, px per decade

    def x(v):
        return x0 + dec * (log10(v) + 1)

    rows_y = [78, 168, 258]
    axis_y = 306
    ref = x(PB[0][2])
    parts = [
        '<svg class="viz viz-pb" viewBox="0 0 1120 372" role="img" '
        'aria-labelledby="pb-title pb-desc">',
        '<title id="pb-title">Detection limit for lead in copper alloys</title>',
        '<desc id="pb-desc">LIBS 200 ppm; RLA-LIF 8 ppm (25 times lower); '
        'LA-LIF 0.2 ppm (1000 times lower). Log scale.</desc>',
    ]
    # decade gridlines + ticks
    for v, lab in [(0.1, "0.1"), (1, "1"), (10, "10"), (100, "100"), (1000, "1000")]:
        parts.append(f'<line class="grid" x1="{f(x(v))}" x2="{f(x(v))}" y1="30" y2="{axis_y}"/>')
        parts.append(f'<text class="tick" x="{f(x(v))}" y="{axis_y + 26}" text-anchor="middle">{lab}</text>')
    parts.append(f'<line class="axis" x1="{x0}" x2="{f(x(1000))}" y1="{axis_y}" y2="{axis_y}"/>')
    parts.append(
        f'<text class="axis-title" x="{f((x0 + x(1000)) / 2)}" y="{axis_y + 58}" text-anchor="middle">'
        "Detection limit for Pb (ppm, log scale)</text>"
    )

    for i, ((name, sub, dl), y) in enumerate(zip(PB, rows_y)):
        parts.append(f'<text class="row-label" x="0" y="{y - 4}">{name}</text>')
        parts.append(f'<text class="row-sub" x="0" y="{y + 20}">{sub}</text>')
        parts.append(f'<line class="row-rule" x1="{x0}" x2="{f(x(1000))}" y1="{y}" y2="{y}"/>')
        xv = x(dl)
        val = f"{dl:g} ppm"
        if i == 0:
            parts.append(
                f'<g class="anim-pop" style="--d:.15s"><circle class="dot dot-ref" cx="{f(xv)}" cy="{y}" r="9">'
                f'<title>LIBS: {val}</title></circle></g>'
            )
            parts.append(f'<text class="value" x="{f(xv)}" y="{y - 20}" text-anchor="middle">{val}</text>')
            continue
        ratio = PB[0][2] / dl
        length = ref - xv
        d = 0.35 + 0.55 * (i - 1)
        parts.append(f'<circle class="ghost" cx="{f(ref)}" cy="{y}" r="8"/>')
        parts.append(
            f'<line class="connector anim-draw" x1="{f(ref)}" x2="{f(xv)}" y1="{y}" y2="{y}" '
            f'style="--len:{f(length)};--d:{d:.2f}s"/>'
        )
        parts.append(
            f'<g class="anim-slide" style="--dx:{f(length)}px;--d:{d:.2f}s">'
            f'<circle class="dot dot-hi" cx="{f(xv)}" cy="{y}" r="10">'
            f'<title>{name}: {val} ({ratio:g}× lower than LIBS)</title></circle></g>'
        )
        parts.append(
            f'<text class="value anim-fade" style="--d:{d + 1.0:.2f}s" x="{f(xv)}" y="{y - 22}" '
            f'text-anchor="middle">{val}</text>'
        )
        parts.append(
            f'<text class="ratio anim-fade" style="--d:{d + 1.0:.2f}s" x="{f((ref + xv) / 2)}" y="{y - 14}" '
            f'text-anchor="middle">{ratio:g}× lower</text>'
        )
    parts.append("</svg>")
    write("pb-detection-limits", "\n".join(parts))


# ---------------------------------------------------------------------------
# 2. Underwater LIBS: LOD vs CO2 pressure (dodged dot plot, log scale)
#    Source: Goueguel et al., Opt. Laser Technol. 108 (2018) 53-58, Table.
# ---------------------------------------------------------------------------
PRESSURES = ["10 bar", "200 bar", "400 bar"]
LOD = {  # element: [(LOD, sd) at 10, 200, 400 bar], ppm
    "Ca": [(2.5, 0.7), (2.5, 0.6), (2.7, 0.3)],
    "Sr": [(3.3, 0.1), (3.0, 0.1), (3.4, 0.3)],
    "Ba": [(4.4, 0.2), (4.9, 0.1), (3.9, 0.5)],
    "Mn": [(10.5, 0.1), (7.4, 0.1), (5.2, 0.1)],
    "Mg": [(31.7, 0.9), (31.1, 0.8), (30.8, 1.1)],
}


def lod_chart():
    x0, dec = 120, 400  # x of 1 ppm, px per decade

    def x(v):
        return x0 + dec * log10(v)

    top, row_h = 66, 60
    axis_y = top + row_h * len(LOD) - 8
    parts = [
        '<svg class="viz viz-lod" viewBox="0 0 1120 420" role="img" '
        'aria-labelledby="lod-title lod-desc">',
        '<title id="lod-title">Limits of detection versus CO2 pressure</title>',
        '<desc id="lod-desc">LODs for Ca, Sr, Ba, Mn and Mg at 10, 200 and 400 bar of CO2. '
        'Values change little with pressure; Mn improves from 10.5 to 5.2 ppm.</desc>',
    ]
    # legend
    lx = 640
    parts.append(f'<text class="legend-title" x="{lx - 14}" y="22" text-anchor="end">CO₂ pressure</text>')
    for k, p in enumerate(PRESSURES):
        parts.append(f'<circle class="p{k}" cx="{lx + k * 120}" cy="16" r="7"/>')
        parts.append(f'<text class="legend" x="{lx + 14 + k * 120}" y="22">{p}</text>')
    # grid
    for v in [1, 2, 5, 10, 20, 50, 100]:
        cls = "grid" if v in (1, 10, 100) else "grid grid-minor"
        parts.append(f'<line class="{cls}" x1="{f(x(v))}" x2="{f(x(v))}" y1="{top - 26}" y2="{axis_y}"/>')
        parts.append(f'<text class="tick" x="{f(x(v))}" y="{axis_y + 26}" text-anchor="middle">{v}</text>')
    parts.append(f'<line class="axis" x1="{x0}" x2="{f(x(100))}" y1="{axis_y}" y2="{axis_y}"/>')
    parts.append(
        f'<text class="axis-title" x="{f((x0 + x(100)) / 2)}" y="{axis_y + 56}" text-anchor="middle">'
        "Limit of detection (ppm, log scale)</text>"
    )
    parts.append(f'<text class="col-head" x="1120" y="{top - 30}" text-anchor="end">range</text>')

    for i, (el, vals) in enumerate(LOD.items()):
        yc = top + i * row_h + row_h / 2 - 22
        parts.append(f'<text class="row-label" x="0" y="{f(yc + 9)}">{el}</text>')
        lo = min(v for v, _ in vals)
        hi = max(v for v, _ in vals)
        parts.append(
            f'<text class="range" x="1120" y="{f(yc + 7)}" text-anchor="end">{lo:g}–{hi:g} ppm</text>'
        )
        for k, (v, sd) in enumerate(vals):
            y = yc + (k - 1) * 13
            d = 0.2 + i * 0.16 + k * 0.06
            parts.append(
                f'<g class="anim-pop" style="--d:{d:.2f}s">'
                f'<line class="err p{k}-stroke" x1="{f(x(v - sd))}" x2="{f(x(v + sd))}" y1="{f(y)}" y2="{f(y)}"/>'
                f'<circle class="dot p{k}" cx="{f(x(v))}" cy="{f(y)}" r="6.5">'
                f"<title>{el} · {PRESSURES[k]}: {v:g} ± {sd:g} ppm</title></circle></g>"
            )
    parts.append("</svg>")
    write("uw-lod-pressure", "\n".join(parts))


# ---------------------------------------------------------------------------
# 3. Emission-line "barcode" for the title slide (decorative, real positions)
# ---------------------------------------------------------------------------
LINES = [  # nm, element (air wavelengths)
    (393.37, "Ca II"), (394.40, "Al I"), (396.15, "Al I"), (396.85, "Ca II"),
    (403.08, "Mn I"), (405.78, "Pb I"), (407.77, "Sr II"), (421.55, "Sr II"),
    (422.67, "Ca I"), (455.40, "Ba II"), (460.73, "Sr I"), (493.41, "Ba II"),
    (516.73, "Mg I"), (517.27, "Mg I"), (518.36, "Mg I"), (588.99, "Na I"),
    (589.59, "Na I"), (656.28, "H α"), (670.78, "Li I"), (766.49, "K I"), (769.90, "K I"),
]
LABELS = [(396.85, "Ca · Al", "end"), (405.78, "Pb", "start"), (421.9, "Sr"), (455.4, "Ba"), (517.3, "Mg"),
          (589.3, "Na"), (656.28, "Hα"), (670.78, "Li"), (768.2, "K")]
LABELS = [lab if len(lab) == 3 else (*lab, "middle") for lab in LABELS]


def wl_rgb(nm):
    """Approximate visible colour of a wavelength (after D. Bruton)."""
    if nm < 440:
        r, g, b = -(nm - 440) / 60, 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, -(nm - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    # keep violet and deep-red ends visible on a dark background
    lift = 0.25 if (nm < 420 or nm > 700) else 0.0
    r, g, b = (min(1, c + lift) for c in (r, g, b))
    return "#{:02x}{:02x}{:02x}".format(*(round(255 * c ** 0.8) for c in (r, g, b)))


def spectrum():
    lo, hi, w = 380, 780, 1200

    def x(nm):
        return (nm - lo) / (hi - lo) * w

    parts = [
        f'<svg class="spectrum" viewBox="0 0 {w} 110" aria-hidden="true">',
        f'<line class="spectrum-base" x1="0" x2="{w}" y1="96" y2="96"/>',
    ]
    for i, (nm, el) in enumerate(LINES):
        parts.append(
            f'<line class="spectrum-line" style="--d:{0.15 + i * 0.05:.2f}s" x1="{f(x(nm))}" x2="{f(x(nm))}" '
            f'y1="96" y2="26" stroke="{wl_rgb(nm)}"><title>{el} {nm} nm</title></line>'
        )
    for nm, lab, anchor in LABELS:
        parts.append(f'<text class="spectrum-label" x="{f(x(nm))}" y="16" text-anchor="{anchor}">{lab}</text>')
    parts.append("</svg>")
    write("spectrum-lines", "\n".join(parts))


if __name__ == "__main__":
    pb_chart()
    lod_chart()
    spectrum()
    print("charts written to", OUT)

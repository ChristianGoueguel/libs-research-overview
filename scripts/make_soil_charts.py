"""Inline-SVG charts for the soil-texture (PLSR vs elastic net) slides.

Run from the project root:  python3 scripts/make_soil_charts.py
Inputs (extracted read-only from Granulo_pls_enet.RData, see scripts/extract_soil_results.R):
  data/soil-texture/results.json  tuning results, CV resamples, test-set predictions
  data/soil-texture/vip.json      PLSR VIP profiles on the calibrated wavelength axis
Outputs: assets/charts/_soil-*.md (raw-HTML blocks pulled in with {{< include >}}).
"""

import json
from math import log10, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "charts"
DATA = ROOT / "data" / "soil-texture"


def build_vip(bin_size=4):
    """Reduce full-resolution VIP (coefs.json) to 4-pixel max bins on the calibrated wavelength axis."""
    import csv
    co = json.loads((DATA / "coefs.json").read_text())
    wl = [float(r["wavelength"]) for r in csv.DictReader((DATA / "wavelength-calibration.csv").open())]
    out = {"binSize": bin_size, "wavelength": [], "meanSpectrum": [], "VIP": {f: [] for f in ("sand", "silt", "clay")}}
    for i in range(0, len(wl), bin_size):
        j = min(len(wl), i + bin_size)
        out["wavelength"].append(round(sum(wl[i:j]) / (j - i), 3))
        out["meanSpectrum"].append(round(max(co["meanSpectrum"][i:j]), 1))
        for f in out["VIP"]:
            out["VIP"][f].append(round(max(co[f]["VIP"][i:j]), 3))
    (DATA / "vip.json").write_text(json.dumps(out, separators=(",", ":")))


if (DATA / "coefs.json").exists():
    build_vip()
RES = json.loads((DATA / "results.json").read_text())
VIP = json.loads((DATA / "vip.json").read_text())

FRACTIONS = ["sand", "silt", "clay"]
TITLES = {"sand": "Sand", "silt": "Silt", "clay": "Clay"}
N_RESAMPLES = 50


def write(name, svg):
    (OUT / f"_{name}.md").write_text("```{=html}\n" + svg.strip() + "\n```\n")


def f1(v):
    return f"{v:.1f}"


def nice_ticks(lo, hi, n=5):
    span = hi - lo
    raw = span / n
    mag = 10 ** int(f"{raw:e}".split("e")[1])
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=raw)
    start = (lo // step) * step
    ticks, t = [], start
    while t <= hi + 1e-9:
        if t >= lo - 1e-9:
            ticks.append(round(t, 10))
        t += step
    return ticks


def fmt(v):
    return f"{v:g}" if abs(v) >= 1 or v == 0 else f"{v:.2g}"


class Panel:
    """Maps data coordinates into a rectangle of the SVG."""

    def __init__(self, x, y, w, h, xr, yr, xlog=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xr, self.yr, self.xlog = xr, yr, xlog

    def px(self, v):
        lo, hi = self.xr
        if self.xlog:
            v, lo, hi = log10(v), log10(lo), log10(hi)
        return self.x + (v - lo) / (hi - lo) * self.w

    def py(self, v):
        lo, hi = self.yr
        return self.y + self.h - (v - lo) / (hi - lo) * self.h

    def frame(self, xticks, yticks, xfmt=fmt, yfmt=fmt, xlabel="", ylabel=""):
        p = []
        for t in yticks:
            p.append(f'<line class="grid" x1="{self.x}" x2="{self.x + self.w}" y1="{f1(self.py(t))}" y2="{f1(self.py(t))}"/>')
            p.append(f'<text class="tick" x="{self.x - 8}" y="{f1(self.py(t) + 5)}" text-anchor="end">{yfmt(t)}</text>')
        for t in xticks:
            p.append(f'<text class="tick" x="{f1(self.px(t))}" y="{self.y + self.h + 20}" text-anchor="middle">{xfmt(t)}</text>')
        p.append(f'<line class="axis" x1="{self.x}" x2="{self.x + self.w}" y1="{self.y + self.h}" y2="{self.y + self.h}"/>')
        if xlabel:
            p.append(f'<text class="axis-title" x="{self.x + self.w / 2}" y="{self.y + self.h + 42}" text-anchor="middle">{xlabel}</text>')
        if ylabel:
            p.append(f'<text class="axis-title" x="{self.x - 46}" y="{self.y + self.h / 2}" text-anchor="middle" '
                     f'transform="rotate(-90 {self.x - 46} {self.y + self.h / 2})">{ylabel}</text>')
        return p


def polyline_len(pts):
    return sum(sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) for (x1, y1), (x2, y2) in zip(pts, pts[1:]))


def path(pts):
    return "M" + " L".join(f"{f1(x)},{f1(y)}" for x, y in pts)


def unit(f):
    return "clay<tspan baseline-shift=\"super\" font-size=\"70%\">0.54</tspan> scale" if f == "clay" else "%"


# ---------------------------------------------------------------------------
# 1. PLSR tuning: CV RMSE vs number of latent variables (mean ± 1 SE)
# ---------------------------------------------------------------------------
def pls_tuning():
    parts = ['<svg class="viz viz-soil" viewBox="0 0 1140 330" role="img" aria-label="PLSR cross-validated RMSE versus number of latent variables">']
    for k, fr in enumerate(FRACTIONS):
        t = RES["tune"]["PLSR"][fr]
        nc, rmse, sd, best = t["ncomp"], t["RMSE"], t["RMSESD"], t["best"]
        se = [s / sqrt(N_RESAMPLES) for s in sd]
        lo = min(r - e for r, e in zip(rmse, se))
        hi = max(r + e for r, e in zip(rmse, se))
        yt = nice_ticks(lo, hi, 4)
        P = Panel(70 + k * 385, 46, 290, 220, (1, 20), (min(yt[0], lo), max(yt[-1], hi)))
        parts.append(f'<text class="panel-title" x="{P.x - 60}" y="20">{TITLES[fr]}</text>')
        parts.append(f'<text class="panel-sub" x="{P.x - 60 + len(TITLES[fr]) * 12 + 10}" y="20">CV RMSE, {unit(fr)}</text>')
        parts += P.frame([1, 5, 10, 15, 20], yt, xlabel="latent variables" if k == 1 else "")
        upper = [(P.px(c), P.py(r + e)) for c, r, e in zip(nc, rmse, se)]
        lower = [(P.px(c), P.py(r - e)) for c, r, e in zip(nc, rmse, se)][::-1]
        parts.append(f'<path class="band-pls anim-fade" style="--d:.2s" d="{path(upper + lower)} Z"/>')
        pts = [(P.px(c), P.py(r)) for c, r in zip(nc, rmse)]
        parts.append(f'<path class="line-pls anim-draw" style="--len:{f1(polyline_len(pts))};--d:.1s" d="{path(pts)}"/>')
        for c, r, s in zip(nc, rmse, sd):
            parts.append(f'<circle class="pt-pls-sm" cx="{f1(P.px(c))}" cy="{f1(P.py(r))}" r="3"><title>{c} LV: RMSE {r:.3g} (SD {s:.2g})</title></circle>')
        bi = nc.index(best)
        bx, by = P.px(best), P.py(rmse[bi])
        parts.append(f'<g class="anim-pop" style="--d:1.1s"><circle class="dot pt-pls" cx="{f1(bx)}" cy="{f1(by)}" r="8">'
                     f'<title>Selected: {best} latent variables, CV RMSE {rmse[bi]:.3g}</title></circle></g>')
        parts.append(f'<text class="callout anim-fade" style="--d:1.3s" x="{f1(bx + 10)}" y="{f1(by - 14)}">{best} LVs</text>')
    parts.append("</svg>")
    write("soil-tuning-pls", "\n".join(parts))


# ---------------------------------------------------------------------------
# 2. Elastic-net tuning: interactive 3D surface of CV RMSE over the alpha x lambda grid
#    (Plotly gl3d, loaded once in the deck header; drawn when its tab becomes visible)
# ---------------------------------------------------------------------------
CAP = 1.6  # z is capped at CAP x the optimum so the valley stays readable
N_LAMBDA = {"sand": 1000, "silt": 1000, "clay": 500}  # full lambda grid per fraction (elasticnetGrid.2 / .1)


def enet_surface():
    data = {}
    for fr in FRACTIONS:
        t = RES["tune"]["ENET"][fr]
        curves = sorted(t["curves"], key=lambda c: c["alpha"])
        alphas = [c["alpha"] for c in curves]
        lam = curves[0]["lambda"]
        z = [c["RMSE"] for c in curves]
        best = min(min(r) for r in z)
        res = RES["resample"]["ENET"][fr]
        m = sum(res) / len(res)
        se = sqrt(sum((v - m) ** 2 for v in res) / (len(res) - 1)) / sqrt(len(res))
        cells = [r for row in z for r in row]
        within = sum(r <= best + se for r in cells) / len(cells)
        logalpha = fr != "clay"
        unit_txt = "clay^0.54" if fr == "clay" else "%"
        data[fr] = {
            "x": lam,
            "y": [log10(a) if logalpha else a for a in alphas],
            "alpha": alphas,
            "z": [[min(r, best * CAP) for r in row] for row in z],
            "text": [[f"α = {a:g}<br>λ = {l:.3g}<br>CV RMSE = {r:.3g} {unit_txt}" for l, r in zip(lam, row)]
                     for a, row in zip(alphas, z)],
            "logAlpha": logalpha,
            "best": {"alpha": t["bestAlpha"], "lambda": t["bestLambda"], "rmse": round(best, 4),
                     "y": log10(t["bestAlpha"]) if logalpha else t["bestAlpha"]},
            "cap": round(best * CAP, 3),
            "se": round(se, 4),
            "within": round(100 * within),
            "unit": "clay<sup>0.54</sup> scale" if fr == "clay" else "%",
            "zTitle": "CV RMSE (clay^0.54)" if fr == "clay" else "CV RMSE (%)",
        }
    side = "".join(
        f'<div class="enet3d-info" data-f="{fr}"{"" if i == 0 else " hidden"}>'
        f'<div class="kicker">{TITLES[fr]}</div>'
        f'<div class="enet3d-stat"><b>α = {d["best"]["alpha"]:g}</b> · λ = {d["best"]["lambda"]:.3g}</div>'
        f'<div class="enet3d-note">selected (lowest CV RMSE = {d["best"]["rmse"]:.3g} {d["unit"]})</div>'
        f'<div class="enet3d-stat"><b>{d["within"]} %</b> of the grid</div>'
        f'<div class="enet3d-note">lies within 1 standard error (±{d["se"]:.2g}) of the optimum</div>'
        f'<div class="enet3d-note">{len(d["alpha"])} α × {N_LAMBDA[fr]:,} λ values tested; surface shows 100 λ per α</div>'
        "</div>"
        for i, (fr, d) in enumerate(data.items()))
    buttons = "".join(f'<button type="button" class="{"on" if i == 0 else ""}" data-f="{fr}">{TITLES[fr]}</button>'
                      for i, fr in enumerate(FRACTIONS))
    html = f"""<div class="enet3d">
  <div class="enet3d-main">
    <div class="enet3d-controls">{buttons}<span class="enet3d-hint">drag to rotate · scroll disabled</span></div>
    <div class="enet3d-plot" id="enet3d-plot" role="img" aria-label="3D surface of elastic-net cross-validated RMSE over alpha and lambda"></div>
  </div>
  <div class="enet3d-side">{side}</div>
</div>
<script type="application/json" id="enet3d-data">{json.dumps(data, separators=(",", ":"))}</script>
<script>
(function () {{
  const el = document.getElementById('enet3d-plot');
  const data = JSON.parse(document.getElementById('enet3d-data').textContent);
  // low error = dark (the valley floor reads as the target); high error fades out
  const scale = [[0, '#0d366b'], [0.15, '#1c5cab'], [0.35, '#3987e5'], [0.6, '#86b6ef'], [1, '#e6f0fc']];
  let current = 'sand', drawn = false;
  const font = {{ family: 'IBM Plex Sans, Helvetica Neue, Arial, sans-serif', size: 12, color: '#1c2333' }};
  function alphaTicks(d) {{
    if (!d.logAlpha) return {{ title: {{ text: 'α' }} }};
    const v = [1e-4, 1e-3, 1e-2, 1e-1, 1];
    return {{ title: {{ text: 'α (log scale)' }}, tickvals: v.map(Math.log10), ticktext: v.map(String) }};
  }}
  function build(f) {{
    const d = data[f];
    const surface = {{
      type: 'surface', x: d.x, y: d.y, z: d.z, text: d.text, hovertemplate: '%{{text}}<extra></extra>',
      colorscale: scale, cmin: d.best.rmse, cmax: d.cap, showscale: true,
      colorbar: {{ title: {{ text: 'CV RMSE', side: 'right' }}, thickness: 12, len: 0.6, x: 1.0, tickfont: font }},
      contours: {{ z: {{ show: true, usecolormap: true, highlightcolor: '#eb6834', project: {{ z: true }} }} }},
      lighting: {{ ambient: 0.75, diffuse: 0.6, specular: 0.15, roughness: 0.9 }}
    }};
    const opt = {{
      type: 'scatter3d', mode: 'markers+text', x: [d.best.lambda], y: [d.best.y], z: [d.best.rmse],
      marker: {{ size: 7, color: '#eb6834', line: {{ color: '#ffffff', width: 2 }}, symbol: 'diamond' }},
      text: ['<b>optimum</b>'], textposition: 'top center', textfont: {{ family: font.family, size: 14, color: '#f76707' }},
      hovertemplate: 'Selected<br>α = ' + d.best.alpha + '<br>λ = ' + d.best.lambda.toPrecision(3) + '<br>CV RMSE = ' + d.best.rmse.toPrecision(3) + '<extra></extra>'
    }};
    const axis = {{ gridcolor: '#dfe3ea', zerolinecolor: '#c3c2b7', showbackground: true, backgroundcolor: '#f4f6fa', tickfont: font }};
    const layout = {{
      margin: {{ l: 0, r: 0, t: 0, b: 0 }}, paper_bgcolor: 'rgba(0,0,0,0)', font: font, showlegend: false,
      scene: {{
        xaxis: Object.assign({{ title: {{ text: 'λ (penalty strength)' }} }}, axis),
        yaxis: Object.assign(alphaTicks(d), axis),
        zaxis: Object.assign({{ title: {{ text: d.zTitle }}, range: [d.best.rmse - (d.cap - d.best.rmse) * 0.05, d.cap] }}, axis),
        camera: {{ eye: {{ x: -1.3, y: -1.38, z: 0.68 }}, center: {{ x: 0.02, y: 0, z: -0.08 }} }},
        aspectmode: 'manual', aspectratio: {{ x: 1.35, y: 1, z: 0.7 }}
      }}
    }};
    return [[surface, opt], layout];
  }}
  function draw() {{
    if (!window.Plotly) return;
    const [traces, layout] = build(current);
    Plotly.react(el, traces, layout, {{ displayModeBar: false, scrollZoom: false, responsive: true }});
    drawn = true;
  }}
  new ResizeObserver(() => {{
    if (el.clientWidth === 0) return;
    if (!drawn) draw(); else Plotly.Plots.resize(el);
  }}).observe(el);
  el.closest('.enet3d').querySelectorAll('.enet3d-controls button').forEach((b) => b.addEventListener('click', () => {{
    current = b.dataset.f;
    b.parentNode.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
    el.closest('.enet3d').querySelectorAll('.enet3d-info').forEach((x) => (x.hidden = x.dataset.f !== current));
    draw();
  }}));
}})();
</script>"""
    write("soil-enet-surface", html)


# ---------------------------------------------------------------------------
# 3. Test set: predicted vs measured (both learners, 1:1 line)
# ---------------------------------------------------------------------------
def metrics(o, p):
    n = len(o)
    rmse = sqrt(sum((b - a) ** 2 for a, b in zip(o, p)) / n)
    mo, mp = sum(o) / n, sum(p) / n
    cov = sum((a - mo) * (b - mp) for a, b in zip(o, p))
    r2 = cov ** 2 / (sum((a - mo) ** 2 for a in o) * sum((b - mp) ** 2 for b in p))
    return rmse, r2


def diamond(x, y, s=6.5):
    return f"M{f1(x)},{f1(y - s)} L{f1(x + s)},{f1(y)} L{f1(x)},{f1(y + s)} L{f1(x - s)},{f1(y)} Z"


def pred_obs():
    parts = ['<svg class="viz viz-soil" viewBox="0 0 1140 400" role="img" aria-label="Predicted versus measured sand, silt and clay on the independent test set">']
    for k, fr in enumerate(FRACTIONS):
        d = RES["test"][fr]
        o, pp, pe, ids = d["obs"], d["PLSR"], d["ENET"], d["sample"]
        top = max(o + pp + pe)
        hi = {"sand": 100, "silt": 80, "clay": 60}[fr]
        hi = max(hi, (int(top // 10) + 1) * 10)
        lo = min(0, (min(o + pp + pe) // 5) * 5)
        ticks = nice_ticks(0, hi, 4)
        P = Panel(70 + k * 385, 30, 290, 290, (lo, hi), (lo, hi))
        parts.append(f'<text class="panel-title" x="{P.x - 60}" y="16">{TITLES[fr]} (%)</text>')
        parts += P.frame(ticks, ticks, xlabel="measured (%)", ylabel="predicted (%)" if k == 0 else "")
        parts.append(f'<line class="ref-line" x1="{P.px(lo)}" y1="{P.py(lo)}" x2="{P.px(hi)}" y2="{P.py(hi)}"/>')
        parts.append(f'<text class="annot" x="{f1(P.px(hi) - 4)}" y="{f1(P.py(hi) + 16)}" text-anchor="end">1:1</text>')
        for i, (a, b, c, sid) in enumerate(zip(o, pp, pe, ids)):
            dl = 0.25 + i * 0.02
            parts.append(f'<path class="pt-enet anim-pop" style="--d:{dl + 0.35:.2f}s" d="{diamond(P.px(a), P.py(c))}">'
                         f'<title>{sid} · elastic net: measured {a:g}, predicted {c:g}</title></path>')
            parts.append(f'<circle class="pt-pls anim-pop" style="--d:{dl:.2f}s" cx="{f1(P.px(a))}" cy="{f1(P.py(b))}" r="5.5">'
                         f'<title>{sid} · PLSR: measured {a:g}, predicted {b:g}</title></circle>')
        for j, (lab, pred, cls) in enumerate((("PLSR", pp, "pls"), ("Elastic net", pe, "enet"))):
            rmse, r2 = metrics(o, pred)
            y = P.y + 18 + j * 22
            mark = (f'<circle class="pt-{cls}" cx="{P.x + 14}" cy="{y - 5}" r="5"/>' if cls == "pls"
                    else f'<path class="pt-{cls}" d="{diamond(P.x + 14, y - 5, 5.5)}"/>')
            parts.append(mark + f'<text class="annot" x="{P.x + 26}" y="{y}"><tspan class="annot-strong">{lab}</tspan>'
                                f'  RMSE {rmse:.1f} · R² {r2:.2f}</text>')
    parts.append("</svg>")
    write("soil-pred-obs", "\n".join(parts))


# ---------------------------------------------------------------------------
# 4. CV resample distributions (50 resamples per learner)
# ---------------------------------------------------------------------------
def cv_resamples():
    parts = ['<svg class="viz viz-soil" viewBox="0 0 1140 320" role="img" aria-label="Distribution of cross-validated RMSE over 50 resamples for PLSR and elastic net">']
    for k, fr in enumerate(FRACTIONS):
        a, b = RES["resample"]["PLSR"][fr], RES["resample"]["ENET"][fr]
        lo, hi = min(a + b), max(a + b)
        yt = nice_ticks(lo, hi, 4)
        P = Panel(70 + k * 385, 40, 290, 230, (0, 2), (min(yt[0], lo), max(yt[-1], hi)))
        parts.append(f'<text class="panel-title" x="{P.x - 60}" y="16">{TITLES[fr]}</text>')
        parts.append(f'<text class="panel-sub" x="{P.x - 60 + len(TITLES[fr]) * 12 + 10}" y="16">CV RMSE, {unit(fr)}</text>')
        parts += P.frame([], yt)
        for j, (vals, cls, lab) in enumerate(((a, "pls", "PLSR"), (b, "enet", "Elastic net"))):
            cx = P.px(0.5 + j)
            parts.append(f'<text class="tick" x="{f1(cx)}" y="{P.y + P.h + 22}" text-anchor="middle">{lab}</text>')
            order = sorted(range(len(vals)), key=lambda i: vals[i])
            for rank, i in enumerate(order):
                jit = ((rank * 7) % 11 - 5) * 7.5
                shape = (f'<circle class="pt-{cls} pt-light" cx="{f1(cx + jit)}" cy="{f1(P.py(vals[i]))}" r="4.5">' if cls == "pls"
                         else f'<path class="pt-{cls} pt-light" d="{diamond(cx + jit, P.py(vals[i]), 5)}">')
                close = "</circle>" if cls == "pls" else "</path>"
                parts.append(f'<g class="anim-pop" style="--d:{0.2 + rank * 0.012 + j * 0.3:.2f}s">{shape}<title>{lab}: {vals[i]:.3g}</title>{close}</g>')
            m = sum(vals) / len(vals)
            sd = sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
            parts.append(f'<line class="mean-bar anim-fade" style="--d:1.2s" x1="{f1(cx - 52)}" x2="{f1(cx + 52)}" y1="{f1(P.py(m))}" y2="{f1(P.py(m))}"/>')
            parts.append(f'<text class="callout anim-fade" style="--d:1.3s" x="{f1(cx + 58)}" y="{f1(P.py(m) + 5)}">{m:.2f}</text>')
    parts.append("</svg>")
    write("soil-cv-resamples", "\n".join(parts))


# ---------------------------------------------------------------------------
# 5. PLSR variable importance (VIP) on the calibrated wavelength axis
# ---------------------------------------------------------------------------
LABELS = {
    "sand": [(251.43, "Si I 251.4"), (288.16, "Si I 288.2"), (309.27, "Al I 309.3"), (396.15, "Al I 396.2"),
             (589.0, "Na I 589.0"), (656.28, "Hα 656.3")],
    "silt": [(247.86, "C I 247.9"), (251.43, "Si I 251.4"), (288.16, "Si I 288.2"), (589.0, "Na I 589.0"), (656.28, "Hα 656.3")],
    "clay": [(309.27, "Al I 309.3"), (372.0, "Fe I 372.0"), (396.15, "Al I 396.2"), (766.49, "K I 766.5")],
}


def vip_chart(fr):
    wl, vip, spec = VIP["wavelength"], VIP["VIP"][fr], VIP["meanSpectrum"]
    top = (int(max(vip) * 2) + 1) / 2
    P = Panel(70, 44, 1050, 195, (200, 800), (0, top))
    S = Panel(70, 262, 1050, 48, (200, 800), (0, max(spec)))
    parts = [f'<svg class="viz viz-vip" viewBox="0 0 1140 350" role="img" aria-label="PLSR VIP profile for {fr} across the LIBS spectrum">']
    parts += P.frame([], nice_ticks(0, top, 4), ylabel="VIP")
    parts.append(f'<line class="vip-one" x1="{P.x}" x2="{P.x + P.w}" y1="{f1(P.py(1))}" y2="{f1(P.py(1))}"/>')
    parts.append(f'<text class="annot" x="{P.x + P.w - 4}" y="{f1(P.py(1) - 6)}" text-anchor="end">VIP = 1</text>')
    pts = [(P.px(w), P.py(v)) for w, v in zip(wl, vip)]
    parts.append(f'<path class="line-vip anim-fade" style="--d:.1s" d="{path(pts)}"/>')
    sp = [(S.px(w), S.py(v)) for w, v in zip(wl, spec)]
    parts.append(f'<path class="spec-area" d="{path([(S.px(200), S.py(0))] + sp + [(S.px(800), S.py(0))])} Z"/>')
    parts.append(f'<text class="annot" x="{S.x + 6}" y="{S.y + 12}">mean LIBS spectrum</text>')
    for t in range(200, 801, 100):
        parts.append(f'<text class="tick" x="{f1(S.px(t))}" y="{S.y + S.h + 20}" text-anchor="middle">{t}</text>')
    parts.append(f'<text class="axis-title" x="{S.x + S.w / 2}" y="{S.y + S.h + 40}" text-anchor="middle">wavelength (nm)</text>')
    placed = []
    for i, (w0, lab) in enumerate(LABELS[fr]):
        j = max((j for j in range(len(wl)) if abs(wl[j] - w0) < 0.6), key=lambda j: vip[j])
        x, y = P.px(wl[j]), P.py(vip[j])
        ly, w = y - 14, len(lab) * 7.6
        moved = True
        while moved:
            moved = False
            for px_, py_, pw in placed:
                if abs(px_ - x) < (w + pw) / 2 + 8 and abs(py_ - ly) < 17:
                    ly, moved = py_ - 18, True
        placed.append((x, ly, w))
        parts.append(f'<g class="anim-fade" style="--d:{0.6 + i * 0.12:.2f}s"><line class="leader" x1="{f1(x)}" x2="{f1(x)}" y1="{f1(y - 3)}" y2="{f1(ly + 4)}"/>'
                     f'<text class="callout" x="{f1(x)}" y="{f1(ly)}" text-anchor="middle">{lab}</text></g>')
    parts.append("</svg>")
    write(f"soil-vip-{fr}", "\n".join(parts))


if __name__ == "__main__":
    pls_tuning()
    enet_surface()
    pred_obs()
    cv_resamples()
    for fr in FRACTIONS:
        vip_chart(fr)
    print("soil charts written to", OUT)

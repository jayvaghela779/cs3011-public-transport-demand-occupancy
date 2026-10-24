"""Visual design for the dashboard: colours, fonts, page CSS, the Plotly template
and small HTML helpers (headings, figure rows, publication-style tables).

Presentation only. Nothing here reads results or computes metrics; the pages in
streamlit_app.py pass in values they already loaded from the committed files.

Fonts: Newsreader and Overpass (SIL Open Font License 1.1, licences in
app/fonts/) are embedded in the CSS so the local demo looks the same offline.
"""

from __future__ import annotations

import base64
import functools
import html
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

FONTS = Path(__file__).resolve().parent / "fonts"

# Colour tokens. Keep in step with .streamlit/config.toml and web/index.html
# (tests/test_web.py checks that the three theme definitions agree).
INK = "#17212B"
INK_2 = "#4A5562"
INK_3 = "#6B7682"
RULE = "#DCE1E6"
PAPER = "#F3F5F7"
LINE = "#0B6E69"          # route teal: primary colour and the final forecast
LINE_SOFT = "#E4F0EE"
AMBER = "#A86500"         # same hour last week
PLUM = "#6A4FA3"          # historical average
SKY = "#5B8DB8"           # LightGBM alone, mean of last 4 weekdays

SERIES = {"target": INK, "ensemble": LINE, "model": SKY, "seasonal_naive": AMBER,
          "dow4_mean": "#7A8B99", "hist_average": PLUM}
LEVEL_STYLE = {"low": ("#DCEDE7", "#1D5247"), "medium": ("#F3D985", "#5C4300"),
               "high": ("#B23A32", "#FFFFFF")}

SANS = '"Overpass", "Segoe UI", system-ui, -apple-system, sans-serif'
SERIF = '"Newsreader", Georgia, "Times New Roman", serif'

esc = html.escape


# --------------------------------------------------------------------- fonts / CSS

def _font_face(family: str, file: str, weight: str, style: str = "normal",
               ranges: str = "U+0000-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2212") -> str:
    data = base64.b64encode((FONTS / file).read_bytes()).decode("ascii")
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};font-display:swap;"
            f"unicode-range:{ranges};src:url(data:font/woff2;base64,{data}) format('woff2');}}")


CSS = """
:root{--ink:%(INK)s;--ink2:%(INK_2)s;--ink3:%(INK_3)s;--rule:%(RULE)s;--paper:%(PAPER)s;
--line:%(LINE)s;--line-soft:%(LINE_SOFT)s;--amber:%(AMBER)s;--sans:%(SANS)s;--serif:%(SERIF)s}

/* Base */
html,body,[data-testid="stApp"]{font-family:var(--sans);color:var(--ink)}
[data-testid="stApp"]{background:#fff}
[data-testid="stHeader"]{background:transparent}
[data-testid="stMainBlockContainer"]{max-width:1180px;padding:2.75rem 3rem 5rem}
[data-testid="stMain"] p,[data-testid="stMain"] li{font-size:1rem;line-height:1.55}
a{color:var(--line)}
*:focus-visible{outline:2px solid var(--line)!important;outline-offset:2px}

/* Sidebar: masthead, transit-line navigation, study note */
[data-testid="stSidebar"]{background:var(--paper);border-right:1px solid var(--rule)}
[data-testid="stSidebarUserContent"]{padding-top:0}
.mast{display:flex;gap:12px;align-items:flex-start;margin:0 0 30px}
.mast .bullet{flex:0 0 auto;width:38px;height:38px;border-radius:50%%;background:var(--line);color:#fff;
  font:700 15px/38px var(--sans);text-align:center;letter-spacing:.01em;padding-top:1px}
.mast h1{font:500 1.28rem/1.22 var(--serif);margin:0 0 8px;padding:0;color:var(--ink);letter-spacing:-.005em}
.mast p{font-size:.8rem!important;line-height:1.45!important;color:var(--ink2);margin:0}

[data-testid="stSidebar"] [data-testid="stRadio"]>label{display:none}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]{gap:0;width:100%%}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]>div{width:100%%}
[data-testid="stSidebar"] [data-testid="stRadioOption"]{position:relative;width:100%%;margin:0;
  padding:11px 6px 11px 38px;cursor:pointer;border-radius:0}
[data-testid="stSidebar"] [data-testid="stRadioOption"]>div>div:first-child{display:none}
[data-testid="stSidebar"] [data-testid="stRadioOption"]::before{content:"";position:absolute;left:12px;
  top:0;bottom:0;width:4px;background:var(--line)}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]>div:first-child [data-testid="stRadioOption"]::before{top:50%%}
[data-testid="stSidebar"] [data-testid="stRadioGroup"]>div:last-child [data-testid="stRadioOption"]::before{bottom:50%%}
[data-testid="stSidebar"] [data-testid="stRadioOption"]::after{content:"";position:absolute;left:6px;top:50%%;
  width:16px;height:16px;margin-top:-8px;border-radius:50%%;background:#fff;border:3px solid var(--line);
  box-sizing:border-box}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"]::after{left:3px;width:22px;
  height:22px;margin-top:-11px;background:var(--line);border:4px solid #fff;box-shadow:0 0 0 2px var(--line)}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p{font-size:.95rem!important;color:var(--ink2);margin:0}
[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover p{color:var(--ink)}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p{color:var(--ink);font-weight:650}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-focus-visible="true"]{outline:2px solid var(--line);
  outline-offset:-2px}
.side-note{margin:34px 0 0;padding-top:16px;border-top:1px solid var(--rule)}
.side-note p{font-size:.8rem!important;line-height:1.5!important;color:var(--ink2);margin:0 0 8px}
.side-note strong{color:var(--ink);font-weight:600}

/* Page header */
[data-testid="stMain"] [data-testid="stHeading"] h3{font:450 2.55rem/1.1 var(--serif);letter-spacing:-.015em;
  color:var(--ink);padding:0;margin:0}
.deck{font-size:1.12rem!important;line-height:1.5!important;color:var(--ink2);max-width:68ch;margin:6px 0 0}
.mast-m{display:none}
.note{border-left:3px solid var(--amber);padding:1px 0 1px 14px;margin:18px 0 26px;max-width:92ch}
.note p{font-size:.86rem!important;line-height:1.5!important;color:var(--ink2);margin:0}
.note strong{color:var(--ink);font-weight:600}

/* Sections */
.sec{margin:38px 0 4px}
.sec h4{font:500 1.42rem/1.25 var(--serif);color:var(--ink);margin:0;padding:0;letter-spacing:-.005em}
.sec p{font-size:.9rem!important;color:var(--ink2);margin:4px 0 0;max-width:80ch}
.sub{font:500 1.08rem/1.3 var(--serif)!important;color:var(--ink)!important;margin:16px 0 0!important}
.small{font-size:.84rem!important;line-height:1.5!important;color:var(--ink3);max-width:96ch}
.rule{border:0;border-top:1px solid var(--rule);margin:30px 0 0}

/* Route heading and figures */
.route{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:34px 0 4px}
.route .badge{background:var(--line);color:#fff;font:700 1.5rem/1 var(--sans);padding:9px 12px 6px;
  border-radius:4px;font-variant-numeric:tabular-nums;letter-spacing:.01em}
.route .what{font:500 1.42rem/1.2 var(--serif);color:var(--ink)}
.route .when{display:block;font:400 .9rem/1.4 var(--sans);color:var(--ink2);margin-top:3px}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin:18px 0 6px;
  border-top:1px solid var(--ink)}
.fig{padding:14px 22px 6px 0}
.fig+.fig{border-left:1px solid var(--rule);padding-left:22px}
.fig .k{font-size:.84rem;color:var(--ink2);line-height:1.35}
.fig .v{font:650 2.35rem/1.15 var(--sans);color:var(--ink);font-variant-numeric:tabular-nums;margin-top:6px;
  letter-spacing:-.01em}
.fig .v.line{color:var(--line)}
.fig .n{font-size:.8rem;color:var(--ink3);margin-top:2px;line-height:1.4}

/* Publication tables */
.tbl{overflow-x:auto;margin:14px 0 4px}
[data-testid="stMain"] .tbl table,[data-testid="stMain"] .tbl th,[data-testid="stMain"] .tbl td{border-left:0;
  border-right:0;background:transparent}
[data-testid="stMain"] .tbl tr{border:0;background:transparent}
[data-testid="stMain"] .tbl table{border-top:2px solid var(--ink);border-bottom:2px solid var(--ink);margin:0}
[data-testid="stMain"] .tbl .r{text-align:right}
.tbl table{border-collapse:collapse;width:100%%;font-size:.9rem;border-top:1.5px solid var(--ink);
  border-bottom:1.5px solid var(--ink);font-variant-numeric:tabular-nums}
[data-testid="stMain"] .tbl th{border-top:0;font-weight:600;color:var(--ink);text-align:left;padding:9px 12px 7px;white-space:nowrap;
  border-bottom:1px solid var(--ink);vertical-align:bottom}
.tbl thead tr.grp th{border-bottom:0;padding-bottom:0;font-weight:500;color:var(--ink2);font-size:.82rem}
.tbl thead tr.grp th.span span{display:block;border-bottom:1px solid var(--rule);padding-bottom:5px}
[data-testid="stMain"] .tbl td{border-top:0;padding:7px 12px;color:var(--ink);border-bottom:1px solid #EEF1F3;white-space:nowrap}
[data-testid="stMain"] .tbl tbody tr:last-child td{border-bottom:0}
[data-testid="stMain"] .tbl tbody tr:hover td{background:#F7F9FA}
.tbl .r{text-align:right}
.tbl td.b{font-weight:700}
.tbl td.lead{color:var(--ink);font-weight:500}
.tbl .ok{color:var(--line);font-weight:700}
.tbl .no{color:#B23A32;font-weight:700}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:8px;vertical-align:0}

/* Crowding hour strip */
.strip{overflow-x:auto;margin:14px 0 6px}
.strip .g{display:grid;gap:3px;align-items:center;min-width:620px}
.strip .h{font-size:.74rem;color:var(--ink3);text-align:center;font-variant-numeric:tabular-nums}
.strip .lab{font-size:.84rem;color:var(--ink2);padding-right:8px}
.strip .c{height:30px;border-radius:2px;font:650 .74rem/30px var(--sans);text-align:center}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:.82rem;color:var(--ink2);margin:8px 0 0}

/* Widgets */
[data-testid="stWidgetLabel"] p{font-size:.84rem!important;color:var(--ink2);font-weight:500}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"]{display:inline-flex;gap:2px;
  padding:3px;border:1px solid var(--rule);border-radius:7px;background:#fff;flex-wrap:wrap}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"]{
  margin:0;padding:6px 13px 4px;border-radius:5px;cursor:pointer}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"]>div>div:first-child{display:none}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"] p{
  font-size:.88rem!important;color:var(--ink2);margin:0}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"][data-selected="true"]{
  background:var(--ink)}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"][data-selected="true"] p{
  color:#fff;font-weight:600}
[data-testid="stMain"] [data-testid="stRadioGroup"][aria-orientation="horizontal"] [data-testid="stRadioOption"][data-focus-visible="true"]{
  outline:2px solid var(--line);outline-offset:1px}
[data-testid="stExpander"] details{border:1px solid var(--rule);border-radius:6px}
[data-testid="stExpander"] summary p{font-weight:600;font-size:.92rem!important}
[data-testid="stPlotlyChart"]{margin-top:4px}

/* Data page */
.essay{display:grid;grid-template-columns:200px minmax(0,68ch);column-gap:36px;row-gap:22px;margin-top:30px}
.essay dt{font:500 1.12rem/1.35 var(--serif);color:var(--ink);padding-top:1px}
.essay dd{margin:0;font:400 1.06rem/1.62 var(--serif);color:var(--ink)}
.essay dd em{font-style:italic}

@media (max-width: 760px){
  [data-testid="stMainBlockContainer"]{padding:3.6rem 1rem 4rem}
  [data-testid="stMain"] [data-testid="stHeading"] h3{font-size:2rem}
  .mast-m{display:block;font:500 .95rem/1.35 var(--serif);color:var(--ink2);margin:0 0 14px;padding-left:12px;
    border-left:4px solid var(--line)}
  .fig+.fig{border-left:0;padding-left:0;border-top:1px solid var(--rule)}
  .figs{grid-template-columns:1fr}
  .essay{grid-template-columns:1fr;row-gap:6px}
  .essay dd{margin-bottom:16px}
}
""" % dict(INK=INK, INK_2=INK_2, INK_3=INK_3, RULE=RULE, PAPER=PAPER, LINE=LINE, LINE_SOFT=LINE_SOFT,
           AMBER=AMBER, SANS=SANS, SERIF=SERIF)


@functools.lru_cache(maxsize=1)
def stylesheet() -> str:
    """The page's <style> block, fonts included (about 0.4 MB, built once per process)."""
    faces = "".join([
        # The middle dot (U+00B7, used in "137 · I") falls back to the system font: in this
        # Overpass build it renders with zero advance width ("137 ·I").
        _font_face("Overpass", "overpass-latin-wght-normal.woff2", "100 900",
                   ranges="U+0000-00B6,U+00B8-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,"
                          "U+2122,U+2212"),
        _font_face("Newsreader", "newsreader-latin-opsz-normal.woff2", "200 800"),
        _font_face("Newsreader", "newsreader-latin-opsz-italic.woff2", "200 800", "italic"),
    ])
    return f"<style>{faces}{CSS}</style>"


# --------------------------------------------------------------------- Plotly

def _template() -> go.layout.Template:
    axis = dict(showline=True, linecolor="#B8C1CA", ticks="outside", ticklen=4, tickcolor="#B8C1CA",
                showgrid=False, zeroline=False, title=dict(font=dict(size=12, color=INK_2), standoff=10),
                tickfont=dict(size=11.5, color=INK_2), automargin=True)
    yaxis = dict(axis, showline=False, ticks="", showgrid=True, gridcolor="#EBEEF1", gridwidth=1)
    return go.layout.Template(layout=go.Layout(
        font=dict(family=SANS, size=12.5, color=INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=[LINE, AMBER, PLUM, INK, SKY],
        xaxis=axis, yaxis=yaxis,
        legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom", title=None,
                    font=dict(size=12, color=INK_2), bgcolor="rgba(0,0,0,0)", itemwidth=30),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=RULE, font=dict(family=SANS, size=12.5, color=INK)),
        margin=dict(l=8, r=12, t=44, b=8),
        bargap=0.28, bargroupgap=0.08,
    ))


pio.templates["transit"] = _template()
CHART_CONFIG = {"displayModeBar": False, "displaylogo": False, "responsive": True}


def figure(height: int = 360, **layout) -> go.Figure:
    fig = go.Figure()
    # Backgrounds are set on the figure itself: Streamlit replaces them when they
    # come only from the template.
    fig.update_layout(template="transit", height=height, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", legend_traceorder="normal", **layout)
    return fig


# --------------------------------------------------------------------- HTML pieces

def fmt_int(x: float) -> str:
    return f"{x:,.0f}"


def section(title: str, note: str | None = None) -> str:
    sub = f"<p>{note}</p>" if note else ""
    return f'<div class="sec"><h4>{esc(title)}</h4>{sub}</div>'


def deck(text: str) -> str:
    return f'<p class="deck">{text}</p>'


def note(lead: str, rest: str) -> str:
    return f'<div class="note"><p><strong>{esc(lead)}</strong> {esc(rest)}</p></div>'


def figures(items: list[tuple[str, str, str | None]], accent: int | None = None) -> str:
    """A results row: (label, value, small note) per figure, divided by hairlines."""
    cells = []
    for i, (k, v, n) in enumerate(items):
        cls = "v line" if i == accent else "v"
        extra = f'<div class="n">{esc(n)}</div>' if n else ""
        cells.append(f'<div class="fig"><div class="k">{esc(k)}</div><div class="{cls}">{esc(v)}</div>{extra}</div>')
    return f'<div class="figs">{"".join(cells)}</div>'


def table(columns: list[tuple[str, str]], rows: list[list[str]], bold: set[tuple[int, int]] = frozenset(),
          groups: list[tuple[str, int]] | None = None, lead: bool = True) -> str:
    """Publication-style table. columns: (header, 'l' or 'r'); cells are HTML-safe strings
    produced by the caller (numbers, or text passed through esc()). bold: (row, col) to set bold."""
    head = ""
    if groups:
        head += '<tr class="grp">' + "".join(
            f'<th colspan="{n}" class="{"span" if t else ""}"><span>{esc(t)}</span></th>' if t
            else f'<th colspan="{n}"></th>' for t, n in groups) + "</tr>"
    head += "<tr>" + "".join(f'<th class="{"r" if a == "r" else ""}">{esc(h)}</th>' for h, a in columns) + "</tr>"
    body = []
    for i, row in enumerate(rows):
        tds = []
        for j, cell in enumerate(row):
            cls = ["r"] if columns[j][1] == "r" else []
            if (i, j) in bold:
                cls.append("b")
            if j == 0 and lead:
                cls.append("lead")
            tds.append(f'<td class="{" ".join(cls)}">{cell}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="tbl"><table><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


def swatch(colour: str) -> str:
    return f'<span class="sw" style="background:{colour}"></span>'


def crowding_strip(hours: list[str], rows: list[tuple[str, list[str | None]]]) -> str:
    """Hour-by-hour crowding levels; each cell shows the level's initial as well as its colour."""
    n = len(hours)
    grid = f"grid-template-columns:76px repeat({n},minmax(26px,1fr))"
    cells = ['<div></div>'] + [f'<div class="h">{esc(h[:2])}</div>' for h in hours]
    for label, levels in rows:
        cells.append(f'<div class="lab">{esc(label)}</div>')
        for h, lev in zip(hours, levels):
            if lev in LEVEL_STYLE:
                bg, fg = LEVEL_STYLE[lev]
                cells.append(f'<div class="c" style="background:{bg};color:{fg}" title="{esc(label)} {esc(h)}: '
                             f'{esc(lev)}">{esc(lev[0].upper())}</div>')
            else:
                cells.append(f'<div class="c" style="background:#F1F3F5;color:{INK_3}" '
                             f'title="{esc(label)} {esc(h)}: no value">&middot;</div>')
    legend = "".join(f'<span>{swatch(bg)}{esc(k.capitalize())} ({k[0].upper()})</span>'
                     for k, (bg, _) in LEVEL_STYLE.items())
    return (f'<div class="strip"><div class="g" style="{grid}">{"".join(cells)}</div></div>'
            f'<div class="legend">{legend}<span>Hours run along the top, 05 means 05:00 to 05:59.</span></div>')

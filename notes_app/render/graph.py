"""Graphs: function graphs, bar, line and pie charts (pgfplots / TikZ)."""

import math

from ..schema import BarChart, FunctionGraph, LineChart, PieChart
from .inline import inline

_PALETTE = ["blue!70!black", "red!75!black", "teal!80!black", "orange!90!black",
            "violet!80!black", "olive!90!black", "cyan!70!black", "brown!80!black"]


def _num(value: float) -> str:
    return f"{value:g}"


def _axis(options: list[str], body: list[str], legend: list[str]) -> str:
    if any(legend):
        body.append("\\legend{" + ",".join("{" + inline(name) + "}" for name in legend) + "}")
        options.append("legend cell align=left")
        options.append("legend style={at={(1.03,1)}, anchor=north west, draw=none}")
    return "\n".join([
        r"\begin{center}",
        r"\begin{tikzpicture}",
        "\\begin{axis}[\n  " + ",\n  ".join(options) + "\n]",
        *body,
        r"\end{axis}",
        r"\end{tikzpicture}",
        r"\end{center}",
    ])


def _labels(block, options: list[str]) -> None:
    options.append("width=0.75\\linewidth")
    if block.title.strip():
        options.append(f"title={{{inline(block.title)}}}")
    if block.x_label.strip():
        options.append(f"xlabel={{{inline(block.x_label)}}}")
    if block.y_label.strip():
        options.append(f"ylabel={{{inline(block.y_label)}}}")


def function_graph(block: FunctionGraph) -> str:
    options = ["axis lines=middle", "grid=both", "grid style={gray!20}",
               "trig format plots=rad", "unbounded coords=jump",
               "xlabel style={anchor=west}", "ylabel style={anchor=south}",
               "title style={yshift=1.5em}",
               f"xmin={_num(block.x_min)}", f"xmax={_num(block.x_max)}"]
    _labels(block, options)
    if block.y_min is not None:
        options.append(f"ymin={_num(block.y_min)}")
    if block.y_max is not None:
        options.append(f"ymax={_num(block.y_max)}")
    domain = f"{_num(block.x_min)}:{_num(block.x_max)}"
    body = [
        f"\\addplot[{_PALETTE[i % len(_PALETTE)]}, thick, smooth, domain={domain}, samples=200] {{{f.expression}}};"
        for i, f in enumerate(block.functions)
    ]
    return _axis(options, body, [f.label for f in block.functions])


def bar_chart(block: BarChart) -> str:
    options = ["ybar", "xtick=data", "enlarge x limits=0.15", "nodes near coords",
               "every node near coord/.append style={font=\\footnotesize}",
               "xticklabels={" + ",".join("{" + inline(c) + "}" for c in block.categories) + "}"]
    _labels(block, options)
    if all(v >= 0 for s in block.series for v in s.values):
        options.append("ymin=0")
    if len(block.categories) > 6:
        options.append("x tick label style={rotate=35, anchor=east}")
    body = []
    for i, series in enumerate(block.series):
        colour = _PALETTE[i % len(_PALETTE)]
        coords = " ".join(f"({x + 1},{_num(v)})" for x, v in enumerate(series.values))
        body.append(f"\\addplot[fill={colour}!60, draw={colour}] coordinates {{{coords}}};")
    return _axis(options, body, [s.name for s in block.series])


def line_chart(block: LineChart) -> str:
    options = ["grid=major", "grid style={gray!20}"]
    _labels(block, options)
    body = []
    for i, series in enumerate(block.series):
        colour = _PALETTE[i % len(_PALETTE)]
        coords = " ".join(f"({_num(p.x)},{_num(p.y)})" for p in series.points)
        body.append(f"\\addplot[{colour}, thick, mark=*] coordinates {{{coords}}};")
    return _axis(options, body, [s.name for s in block.series])


def pie_chart(block: PieChart) -> str:
    """Drawn directly in TikZ: angles are computed here, so it is exact."""
    slices = [s for s in block.slices if s.value > 0]
    total = sum(s.value for s in slices)
    if total <= 0:
        return ""
    out = [r"\begin{center}", r"\begin{tikzpicture}"]
    if block.title.strip():
        out.append(f"\\node[font=\\bfseries] at (0,3.4) {{{inline(block.title)}}};")
    angle = 90.0
    for i, s in enumerate(slices):
        sweep = 360.0 * s.value / total
        end = angle - sweep  # clockwise from 12 o'clock
        mid = (angle + end) / 2
        colour = _PALETTE[i % len(_PALETTE)]
        percent = f"{100 * s.value / total:.0f}\\,\\%"
        out.append(f"\\fill[{colour}!65, draw=white, thick] (0,0) -- ({angle:.2f}:2.2) "
                   f"arc[start angle={angle:.2f}, end angle={end:.2f}, radius=2.2] -- cycle;")
        label = inline(s.label)
        if sweep >= 25:
            out.append(f"\\node[font=\\small] at ({mid:.2f}:1.45) {{{percent}}};")
        else:  # too thin for a label inside: put the percentage outside
            label = f"{label} ({percent})"
        side = "west" if math.cos(math.radians(mid)) >= 0 else "east"
        out.append(f"\\node[anchor={side}, font=\\small] at ({mid:.2f}:2.4) {{{label}}};")
        angle = end
    out += [r"\end{tikzpicture}", r"\end{center}"]
    return "\n".join(out)

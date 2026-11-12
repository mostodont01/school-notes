from ..schema import Table
from .inline import inline


def table(block: Table) -> str:
    """Rows of uneven length are padded with empty cells, never cut."""
    columns = max([len(block.headers), *(len(row) for row in block.rows)], default=0)
    if columns == 0:
        return ""

    def row(cells: list[str], bold: bool = False) -> str:
        cells = [inline(c) for c in cells] + [""] * (columns - len(cells))
        if bold:
            cells = [f"\\textbf{{{c}}}" if c else "" for c in cells]
        return " & ".join(cells) + r" \\"

    out = [
        r"\begin{center}",
        f"\\begin{{tabularx}}{{\\linewidth}}{{{'X' * columns}}}",
        r"\toprule",
    ]
    if block.headers:
        out += [row(block.headers, bold=True), r"\midrule"]
    out += [row(r) for r in block.rows]
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{center}"]
    return "\n".join(out)

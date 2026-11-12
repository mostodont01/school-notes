from ..schema import ListBlock
from .inline import inline


def list_block(block: ListBlock) -> str:
    """Flat items with levels -> nested itemize/enumerate."""
    env = "enumerate" if block.ordered else "itemize"
    out: list[str] = []
    depth = -1
    for item in block.items:
        # Never jump more than one level deeper than the current one.
        level = min(item.level, depth + 1)
        while depth < level:
            out.append("  " * (depth + 1) + f"\\begin{{{env}}}")
            depth += 1
        while depth > level:
            out.append("  " * depth + f"\\end{{{env}}}")
            depth -= 1
        out.append("  " * (depth + 1) + f"\\item {inline(item.text)}")
    while depth >= 0:
        out.append("  " * depth + f"\\end{{{env}}}")
        depth -= 1
    return "\n".join(out)

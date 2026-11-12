from ..schema import Structure
from .inline import inline


def structure(block: Structure) -> str:
    out = [r"\begin{center}", f"\\chemfig{{{block.chemfig.strip()}}}"]
    if block.caption.strip():
        out.append(f"\\\\[0.5ex] {{\\small {inline(block.caption)}}}")
    out.append(r"\end{center}")
    return "\n".join(out)

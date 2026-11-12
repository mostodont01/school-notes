from ..schema import Paragraph
from .inline import inline


def paragraph(block: Paragraph) -> str:
    # A newline in the text is a line break inside the paragraph.
    lines = [inline(line) for line in block.text.split("\n") if line.strip()]
    return " \\\\\n".join(lines)

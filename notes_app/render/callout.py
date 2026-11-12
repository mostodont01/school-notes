from ..schema import Callout
from .inline import inline

# kind -> (default Czech title, colour)
_KINDS = {
    "definition": ("Definice", "blue"),
    "important": ("Důležité", "red"),
    "example": ("Příklad", "teal"),
    "note": ("Poznámka", "gray"),
}


def callout(block: Callout) -> str:
    default_title, colour = _KINDS[block.kind]
    title = inline(block.title) if block.title.strip() else default_title
    body = " \\\\\n".join(inline(line) for line in block.text.split("\n") if line.strip())
    return (
        f"\\begin{{tcolorbox}}[colback={colour}!4, colframe={colour}!60!black, "
        f"fonttitle=\\bfseries, title={{{title}}}]\n{body}\n\\end{{tcolorbox}}"
    )

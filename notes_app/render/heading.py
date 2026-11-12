from ..schema import Heading
from .inline import inline

_COMMANDS = {1: "section", 2: "subsection", 3: "subsubsection"}


def heading(block: Heading) -> str:
    return f"\\{_COMMANDS[block.level]}*{{{inline(block.text)}}}"

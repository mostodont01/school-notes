from ..schema import Equation


def equation(block: Equation) -> str:
    return f"\\[\n{block.latex.strip()}\n\\]"

from ..schema import Reaction


def reaction(block: Reaction) -> str:
    return f"\\begin{{center}}\n\\ce{{{block.mhchem.strip()}}}\n\\end{{center}}"

from ..schema import Rule


def rule(block: Rule) -> str:
    return r"\noindent\rule{\linewidth}{0.4pt}"

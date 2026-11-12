"""Inline text (plain text + a few tags) -> LaTeX.

Deterministic and forgiving: everything outside the known tags is escaped,
unknown tags are printed literally, unmatched closing tags are dropped and
unclosed tags are closed at the end. So no LLM text can break the compile,
except the raw LaTeX inside <m> and <ce>, which is intentional.
"""

import re

_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_ESCAPE_RE = re.compile(r"[\\&%$#_{}~^]")

# Formatting tags: name -> LaTeX command wrapping the content.
_WRAP = {
    "b": r"\textbf",
    "i": r"\textit",
    "u": r"\uline",
    "red": r"\textcolor{red}",
    "sub": r"\textsubscript",
    "sup": r"\textsuperscript",
}
# Raw tags: content is passed through as LaTeX.
_RAW = {"m": ("$", "$"), "ce": (r"\ce{", "}")}

_TAG_RE = re.compile(r"<(/?)(b|i|u|red|sub|sup|m|ce)>")


def escape(text: str) -> str:
    """Escape LaTeX special characters in plain text."""
    return _ESCAPE_RE.sub(lambda m: _ESCAPES[m.group()], text)


def inline(text: str) -> str:
    """Convert inline text with tags to LaTeX."""
    out: list[str] = []
    stack: list[str] = []
    pos = 0
    while True:
        match = _TAG_RE.search(text, pos)
        if match is None:
            out.append(escape(text[pos:]))
            break
        out.append(escape(text[pos:match.start()]))
        closing, name = match.group(1) == "/", match.group(2)
        pos = match.end()

        if name in _RAW and not closing:
            end = text.find(f"</{name}>", pos)
            raw = text[pos:] if end == -1 else text[pos:end]
            pos = len(text) if end == -1 else end + len(name) + 3
            before, after = _RAW[name]
            if raw.strip():
                out.append(before + raw.strip() + after)
        elif not closing and name in _WRAP:
            out.append(_WRAP[name] + "{")
            stack.append(name)
        elif closing and name in stack:
            # Close everything opened after it too (keeps braces balanced).
            while stack:
                out.append("}")
                if stack.pop() == name:
                    break
        # else: stray closing tag -> dropped
    out.append("}" * len(stack))
    return "".join(out)

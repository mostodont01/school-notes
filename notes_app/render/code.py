from ..schema import Code

# Languages the listings package knows (lowercase name -> listings name).
_LANGUAGES = {
    "python": "Python", "c": "C", "c++": "C++", "cpp": "C++", "java": "Java",
    "sql": "SQL", "bash": "bash", "sh": "sh", "html": "HTML", "xml": "XML",
    "php": "PHP", "matlab": "Matlab", "r": "R", "pascal": "Pascal",
}


def code(block: Code) -> str:
    language = _LANGUAGES.get(block.language.strip().lower())
    options = f"[language={language}]" if language else ""
    # The only thing that can break a listing is its own end marker.
    body = block.code.replace(r"\end{lstlisting}", r"\end {lstlisting}").rstrip("\n")
    return f"\\begin{{lstlisting}}{options}\n{body}\n\\end{{lstlisting}}"

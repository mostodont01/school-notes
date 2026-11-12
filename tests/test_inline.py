from notes_app.render.inline import escape, inline


def test_escapes_specials():
    assert escape("100 % & $5 #1 a_b {x} ~ ^ \\") == (
        r"100 \% \& \$5 \#1 a\_b \{x\} \textasciitilde{} \textasciicircum{} \textbackslash{}"
    )


def test_czech_passes_through():
    assert inline("Příliš žluťoučký kůň") == "Příliš žluťoučký kůň"


def test_tags():
    assert inline("<b>a</b> <i>b</i> <red>c</red>") == r"\textbf{a} \textit{b} \textcolor{red}{c}"
    assert inline("m<sup>2</sup>") == r"m\textsuperscript{2}"


def test_nested_tags():
    assert inline("<b>x <i>y</i></b>") == r"\textbf{x \textit{y}}"


def test_raw_math_and_chem_not_escaped():
    assert inline(r"<m>\frac{a}{b}</m>") == r"$\frac{a}{b}$"
    assert inline("<ce>H2SO4</ce>") == r"\ce{H2SO4}"


def test_broken_tags_never_unbalance_braces():
    for text in ["<b>unclosed", "stray</b>", "<b><i>x</b></i>", "<m>open math", "a < b > c"]:
        out = inline(text)
        assert out.count("{") - out.count(r"\{") == out.count("}") - out.count(r"\}"), text


def test_unknown_tags_are_literal():
    assert inline("<x>hi</x>") == "<x>hi</x>"

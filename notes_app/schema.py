"""The document schema: the single source of truth.

The LLM must return a `Document`; the renderers consume a `Document`.
Field descriptions are part of the LLM's instructions (they end up in the
JSON schema the model is constrained to), so keep them precise.

Text fields marked "inline text" may contain these tags (and nothing else
that is LaTeX): <b> <i> <u> <red> <sub> <sup> <m>inline math</m> <ce>chem</ce>.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

INLINE = (
    "Inline text. Plain text with optional tags: <b>bold</b>, <i>italic</i>, "
    "<u>underline</u>, <red>red</red>, <sub>subscript</sub>, <sup>superscript</sup>, "
    "<m>inline LaTeX math, e.g. \\frac{a}{b}</m>, <ce>inline mhchem, e.g. H2SO4</ce>. "
    "No other LaTeX outside <m> and <ce>."
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Heading(_Model):
    type: Literal["heading"]
    level: Literal[1, 2, 3] = Field(description="1 = main topic, 2 = subtopic, 3 = minor heading.")
    text: str = Field(description=INLINE)


class Paragraph(_Model):
    type: Literal["paragraph"]
    text: str = Field(description=INLINE)


class ListItem(_Model):
    text: str = Field(description=INLINE)
    level: int = Field(
        ge=0, le=3,
        description="Nesting depth: 0 = top level, 1 = sub-item of the previous item, etc.",
    )


class ListBlock(_Model):
    type: Literal["list"]
    ordered: bool = Field(description="True for a numbered list, false for bullets.")
    items: list[ListItem] = Field(
        description="All items of ONE list in order, nested items included (use level). "
        "Consecutive items belong in the same list, never split them."
    )


class Table(_Model):
    type: Literal["table"]
    headers: list[str] = Field(description="Column headers (inline text). Empty list if none.")
    rows: list[list[str]] = Field(description="Rows of cells (inline text).")


class Code(_Model):
    type: Literal["code"]
    language: str = Field(description="Programming language in lowercase (python, c, java, sql, bash, html...), or empty.")
    code: str = Field(description="The code exactly as written, with newlines.")


class Rule(_Model):
    type: Literal["rule"]


class Equation(_Model):
    type: Literal["equation"]
    latex: str = Field(
        description="One displayed equation as LaTeX math (amsmath), without $ or \\[ \\]. "
        "For several aligned lines use \\begin{aligned} ... \\end{aligned}."
    )


class Reaction(_Model):
    type: Literal["reaction"]
    mhchem: str = Field(description="Chemical equation in mhchem syntax WITHOUT \\ce{}, e.g. '2 H2 + O2 -> 2 H2O'.")


class Structure(_Model):
    type: Literal["structure"]
    chemfig: str = Field(description="Structural formula in chemfig syntax WITHOUT \\chemfig{}, e.g. 'H-C(-[2]H)(-[6]H)-H'.")
    caption: str = Field(description="Name of the compound (inline text), or empty.")


class Callout(_Model):
    type: Literal["callout"]
    kind: Literal["definition", "important", "example", "note"]
    title: str = Field(description="Short title (inline text), or empty to use the default for the kind.")
    text: str = Field(description=INLINE)


class FunctionPlot(_Model):
    expression: str = Field(description="Function of x in pgfplots syntax, e.g. 'x^2', 'sin(x)', 'exp(-x)', '2*x+1'. Trig uses radians.")
    label: str = Field(description="Legend label (inline text), or empty.")


class FunctionGraph(_Model):
    type: Literal["function_graph"]
    functions: list[FunctionPlot]
    x_min: float
    x_max: float
    y_min: float | None = Field(description="Lower y limit, or null for automatic.")
    y_max: float | None = Field(description="Upper y limit, or null for automatic.")
    x_label: str
    y_label: str
    title: str


class Series(_Model):
    name: str = Field(description="Series name for the legend, or empty.")
    values: list[float] = Field(description="One value per category.")


class BarChart(_Model):
    type: Literal["bar_chart"]
    categories: list[str]
    series: list[Series]
    x_label: str
    y_label: str
    title: str


class Point(_Model):
    x: float
    y: float


class LineSeries(_Model):
    name: str = Field(description="Series name for the legend, or empty.")
    points: list[Point]


class LineChart(_Model):
    type: Literal["line_chart"]
    series: list[LineSeries]
    x_label: str
    y_label: str
    title: str


class Slice(_Model):
    label: str
    value: float


class PieChart(_Model):
    type: Literal["pie_chart"]
    slices: list[Slice]
    title: str


Block = Annotated[
    Union[
        Heading, Paragraph, ListBlock, Table, Code, Rule, Equation, Reaction,
        Structure, Callout, FunctionGraph, BarChart, LineChart, PieChart,
    ],
    Field(discriminator="type"),
]


class Document(_Model):
    title: str = Field(description="Topic of the lesson (inline text), or empty.")
    subject: str = Field(description="School subject, e.g. 'Fyzika', or empty.")
    date: str = Field(description="Date if the notes mention one, else empty.")
    blocks: list[Block]

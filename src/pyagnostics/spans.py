from dataclasses import dataclass

from rich.console import RenderableType


# Represents a span of codepoints in a source code
@dataclass(eq=True, frozen=True)
class SourceSpan:
    # Starting codepoint index of the span, inclusive
    start: int
    # Ending codepoint index of the span, exclusive
    end: int


@dataclass(eq=True, frozen=True)
class LabeledSpan:
    span: SourceSpan
    label: RenderableType

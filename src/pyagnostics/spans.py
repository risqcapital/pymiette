from dataclasses import dataclass
from typing import Self

from rich.console import RenderableType
from rich.style import Style
from rich.text import Span


# Represents a span of codepoints in a source code
@dataclass(eq=True, frozen=True)
class SourceSpan:
    # Starting codepoint index of the span, inclusive
    start: int
    # Ending codepoint index of the span, exclusive
    end: int

    def styled(self: Self, style: Style | str) -> Span:
        return Span(self.start, self.end, style)


@dataclass(eq=True, frozen=True)
class LabeledSpan:
    span: SourceSpan
    label: RenderableType

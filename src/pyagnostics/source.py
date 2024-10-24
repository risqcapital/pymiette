from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from rich.text import Text

from pyagnostics.protocols import (
    SourceCode,
    SourceCodeHighlighter,
    SourceSpan,
    SpanContents,
    WithSourceCode,
)


@dataclass
class InMemorySpanContents:
    text: Text
    span: SourceSpan
    line: int
    column: int
    line_count: int
    name: str | None


if TYPE_CHECKING:
    _: type[SpanContents] = InMemorySpanContents


@dataclass
class InMemorySource(SourceCode):
    source_code: str
    name: str | None = None

    def read_span(
        self: Self,
        span: SourceSpan,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
    ) -> SpanContents:
        if context_lines_after != 0 or context_lines_before != 0:
            raise NotImplementedError(
                "Context lines are not yet supported in InMemorySource"
            )

        lines = self.source_code.splitlines(keepends=True)

        chars_before = 0

        start_line_idx = None
        for i, line in enumerate(lines):
            if chars_before + len(line) >= span.start:
                start_line_idx = i
                break
            chars_before += len(line)

        if start_line_idx is None:
            raise ValueError("Span start is out of bounds")

        chars_in_lines = 0
        end_line_idx = None
        for i, line in enumerate(lines[start_line_idx:]):
            chars_in_lines += len(line)
            if chars_before + chars_in_lines >= span.end:
                end_line_idx = i + start_line_idx
                break

        if end_line_idx is None:
            raise ValueError("Span end is out of bounds")

        return InMemorySpanContents(
            text=Text("".join(lines[start_line_idx : end_line_idx + 1])),
            span=SourceSpan(chars_before, chars_before + chars_in_lines),
            line=start_line_idx + 1,
            column=0,
            line_count=end_line_idx - start_line_idx,
            name=self.name,
        )


@contextmanager
def attach_diagnostic_source_code(
    source_code: SourceCode, highlighter: SourceCodeHighlighter | None = None
) -> Iterator[None]:
    try:
        yield None
    except Exception as e:
        if isinstance(e, WithSourceCode):
            raise e.with_source_code(source_code, highlighter=highlighter)
        else:
            raise

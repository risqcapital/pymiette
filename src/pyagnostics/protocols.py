from collections.abc import Sequence
from typing import Protocol, Self, runtime_checkable

from rich.console import RenderableType
from rich.text import Text

from pyagnostics.severity import Severity
from pyagnostics.spans import LabeledSpan, SourceSpan


class SpanContents(Protocol):
    @property
    def text(self: Self) -> Text: ...

    @property
    def span(self: Self) -> SourceSpan: ...

    @property
    def line(self: Self) -> int: ...

    @property
    def column(self: Self) -> int: ...

    @property
    def line_count(self: Self) -> int: ...

    @property
    def name(self: Self) -> str | None: ...


class SourceCode(Protocol):
    def read_span(
        self: Self,
        span: SourceSpan,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
    ) -> SpanContents: ...


class SourceCodeHighlighter(Protocol):
    def highlight(self: Self, span_contents: SpanContents) -> SpanContents: ...


@runtime_checkable
class Diagnostic(Protocol):
    @property
    def code(self: Self) -> RenderableType | None: ...

    @property
    def severity(self: Self) -> Severity: ...

    @property
    def notes(self: Self) -> Sequence[RenderableType]: ...

    @property
    def message(self: Self) -> RenderableType | None: ...

    @property
    def source_code(self: Self) -> SourceCode | None: ...

    @property
    def highlighter(self: Self) -> SourceCodeHighlighter | None:
        return None

    @property
    def labels(self: Self) -> Sequence[LabeledSpan]: ...

    @property
    def context(self: Self) -> Sequence[RenderableType]: ...


@runtime_checkable
class WithSourceCode(Protocol):
    def with_source_code(
        self: Self,
        source_code: SourceCode,
        highlighter: SourceCodeHighlighter | None = None,
    ) -> Self: ...

from collections.abc import Iterable, Iterator, MutableSequence, Sequence
from dataclasses import dataclass, field
from typing import Self

from rich.color import Color
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    NewLine,
    RenderableType,
    RenderResult,
    RichCast,
    group,
)
from rich.padding import Padding
from rich.segment import Segment
from rich.style import Style
from rich.styled import Styled
from rich.terminal_theme import DIMMED_MONOKAI
from rich.text import Text
from rich.traceback import Stack, Traceback

from pyagnostics.protocols import Diagnostic
from pyagnostics.severity import Severity
from pyagnostics.spans import LabeledSpan, SourceSpan


@dataclass
class LabeledSourceBlock:
    source: Text
    title: str | None = None
    start_line: int = 1
    start_char_index: int = 0
    labels: Sequence[LabeledSpan] = field(default_factory=list)

    def __rich_console__(
        self: Self, _console: Console, _options: ConsoleOptions
    ) -> RenderResult:
        lines = self.source.split()

        lines_in_src = len(lines)
        line_number_max_len = len(str(lines_in_src + self.start_line))
        line_numbers_padding = " " * (line_number_max_len + 1)

        if self.title is not None:
            yield Segment(line_numbers_padding)
            yield Segment(f"╭─[{self.title}]\n")
        else:
            yield Segment(line_numbers_padding)
            yield Segment("╭───\n")

        src_line_start_index = self.start_char_index

        for i, line in enumerate(lines):
            labels_in_line = [
                label
                for label in self.labels
                if src_line_start_index
                <= label.span.start
                <= src_line_start_index + len(line)
            ]

            labels_in_line = sorted(labels_in_line, key=lambda label: label.span.start)

            yield Segment(
                f"{str(i+self.start_line).rjust(line_number_max_len)}",
                style=Style(dim=True),
            )
            yield Segment(" │ ")
            yield line

            if labels_in_line:
                for j in range(len(labels_in_line) + 1):
                    yield Segment(line_numbers_padding)
                    yield Segment("· ")

                    labels_line_length = 0

                    for k, label in enumerate(
                        labels_in_line[: len(labels_in_line) - j + 1]
                    ):
                        before_len = (
                            label.span.start - src_line_start_index - labels_line_length
                        )
                        # If the label exceeds the line length, truncate it to fit
                        label_len = min(
                            label.span.end - label.span.start, len(line) - before_len
                        )
                        label_before_middle_len = label_len // 2
                        label_after_middle_len = label_len - label_before_middle_len - 1

                        style = Style(
                            color=Color.from_triplet(
                                DIMMED_MONOKAI.ansi_colors[(k % 7) + 1]
                            )
                        )

                        if j == 0:
                            yield Segment(" " * before_len)
                            yield Segment("─" * label_before_middle_len, style)
                            yield Segment("┬", style)
                            yield Segment("─" * label_after_middle_len, style)
                        else:
                            yield Segment(" " * (before_len + label_before_middle_len))
                            if k == len(labels_in_line) - j:
                                yield Segment("╰─ ", style)

                                renderable = label.label
                                if isinstance(label.label, str):
                                    renderable = Text(label.label, end="")

                                yield Styled(renderable, style)
                            else:
                                yield Segment("│", style)
                                yield Segment(" " * label_after_middle_len)

                        labels_line_length += before_len + label_len

                    yield Segment.line()

            src_line_start_index += len(line) + 1

        yield Segment(line_numbers_padding)
        yield Segment("╰───\n")


def next_exc(exc: BaseException) -> BaseException | None:
    if exc.__cause__:
        return exc.__cause__
    elif exc.__context__ and not exc.__suppress_context__:
        return exc.__context__
    else:
        return None


def walk_causes_and_stacks(exc: BaseException) -> Iterator[tuple[BaseException, Stack]]:
    cause: BaseException | None = exc
    stacks = Traceback.extract(type(exc), exc, exc.__traceback__).stacks

    while True:
        assert cause is not None
        yield cause, stacks.pop(0)
        cause = next_exc(cause)
        if cause is None:
            break


@dataclass
class CauseList(ConsoleRenderable):
    header: RenderableType | None
    items: Sequence[RenderableType | None]
    style: Style

    def __rich_console__(
        self: Self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if self.header:
            yield Segment(" × ", style=self.style)  # noqa: RUF001
            lines = console.render_lines(self.header, new_lines=True)
            yield from lines[0]
            for line in lines[1:]:
                yield Segment(" │ ", style=self.style)
                yield from line

        for i, item in enumerate(self.items):
            if item is None:
                yield Segment(" │   ", style=self.style)
                yield NewLine()
                continue

            lines = console.render_lines(item)

            for j, line in enumerate(lines):
                if j == 0:
                    if i < len(self.items) - 1:
                        yield Segment(" ├─▶ ", style=self.style)
                    else:
                        yield Segment(" ╰─▶ ", style=self.style)
                elif i < len(self.items) - 1:
                    yield Segment(" │   ", style=self.style)
                else:
                    yield Segment("     ", style=self.style)
                yield from line
                yield NewLine()


@dataclass
class Report(RichCast):
    diag: Diagnostic
    suppressed_frame_paths: Sequence[str] = field(default_factory=list)

    @group()
    def _render_header(self: Self) -> RenderResult:
        if self.diag.code:
            yield Segment(
                f"{self.diag.severity.title()}: ", style=self.diag.severity.style
            )
            yield Styled(self.diag.code, style=self.diag.severity.style)
            yield NewLine()

    @group()
    def _render_causes(
        self: Self, include_exc_causes: bool = True
    ) -> Iterable[RenderableType]:
        causes: MutableSequence[RenderableType | None] = [*self.diag.context]

        if isinstance(self.diag, BaseException):
            causes_and_stacks: Iterator[tuple[BaseException, Stack]] = (
                walk_causes_and_stacks(self.diag)
            )
            if not include_exc_causes:
                causes_and_stacks = iter([next(causes_and_stacks)])

            first = True
            for exc, stack in causes_and_stacks:
                if first:
                    first = False
                    for frame in stack.frames:
                        if any(
                            frame.filename.startswith(path)
                            for path in self.suppressed_frame_paths
                        ):
                            continue

                        causes.append(
                            f"in File {frame.filename}:{frame.lineno} in {frame.name}"
                        )
                elif isinstance(exc, Diagnostic):
                    cause_report = Report(exc)
                    causes.append(
                        Group(
                            Text.assemble(
                                "Cause" if stack.is_cause else "Context",
                                ": ",
                                style=Severity.ERROR.style,
                                end="",
                            ),
                            Styled(
                                exc.code if exc.code else "unknown",
                                style=exc.severity.style,
                            ),
                            cause_report._render_causes(include_exc_causes=False),
                        )
                    )
                else:
                    causes.append(
                        Group(
                            Text.assemble(
                                "Cause" if stack.is_cause else "Context",
                                ": ",
                                exc.__class__.__module__,
                                ".",
                                exc.__class__.__name__,
                                style=Severity.ERROR.style,
                            ),
                            CauseList(
                                str(exc),
                                [
                                    f"in File {frame.filename}:{frame.lineno} in {frame.name}"
                                    for frame in stack.frames
                                ],
                                style=self.diag.severity.style,
                            ),
                        )
                    )

        yield CauseList(self.diag.message, causes, style=self.diag.severity.style)

    @group()
    def _render_snippets(self: Self) -> Iterable[RenderableType]:
        if self.diag.source_code is None or not self.diag.labels:
            return

        min_char = min(label.span.start for label in self.diag.labels)
        max_char = max(label.span.end for label in self.diag.labels)

        span_contents = self.diag.source_code.read_span(SourceSpan(min_char, max_char))
        if self.diag.highlighter is not None:
            span_contents = self.diag.highlighter.highlight(span_contents)

        yield NewLine()
        yield LabeledSourceBlock(
            span_contents.text,
            title=span_contents.name,
            start_line=span_contents.line,
            start_char_index=span_contents.span.start,
            labels=self.diag.labels,
        )

    @group()
    def _render_notes(self: Self) -> Iterable[RenderableType]:
        if self.diag.notes:
            yield NewLine()
            yield from self.diag.notes

    def __rich__(self: Self) -> RenderableType:
        return Padding(
            Group(
                self._render_header(),
                Padding(
                    Group(
                        self._render_causes(),
                        self._render_snippets(),
                        self._render_notes(),
                    ),
                    pad=(0, 1),
                ),
            ),
            pad=(1, 1),
        )

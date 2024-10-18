import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from rich.abc import RichRenderable
from rich.console import Group, RenderableType, RichCast

from pyagnostics.protocols import Diagnostic, SourceCode, WithSourceCode
from pyagnostics.report import Report
from pyagnostics.severity import Severity
from pyagnostics.spans import LabeledSpan


@dataclass
class DiagnosticError(RichCast, WithSourceCode, Exception):
    severity: Severity = Severity.ERROR
    code: RenderableType | None = None
    message: RenderableType | None = None
    source_code: SourceCode | None = None
    labels: list[LabeledSpan] = dataclasses.field(default_factory=list)
    notes: list[RenderableType] = dataclasses.field(default_factory=list)
    context: list[RenderableType] = dataclasses.field(default_factory=list)

    def with_context(self: Self, context: RenderableType) -> Self:
        self.context.append(context)
        return self

    def with_source_code(self: Self, source_code: SourceCode) -> Self:
        if self.source_code is None:
            self.source_code = source_code
        return self

    def add_note(self: Self, note: str) -> None:
        self.notes.append(note)

    def __rich__(self: Self) -> RenderableType:
        return Report(self)


if TYPE_CHECKING:
    _: type[Diagnostic] = DiagnosticError


class DiagnosticErrorGroup(ExceptionGroup[DiagnosticError], WithSourceCode, RichCast):
    def with_source_code(self: Self, source_code: SourceCode) -> Self:
        for exception in self.exceptions:
            if isinstance(exception, WithSourceCode):
                exception.with_source_code(source_code)

        return self

    def __rich__(
        self: Self,
    ) -> RenderableType:
        return Group(
            *[
                cast(RenderableType, exception)
                for exception in self.exceptions
                if isinstance(exception, RichRenderable)
            ]
        )

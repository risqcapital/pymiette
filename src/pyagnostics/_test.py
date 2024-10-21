from pyagnostics.exceptions import DiagnosticError
from pyagnostics.severity import Severity
from pyagnostics.source import InMemorySource, attach_diagnostic_source_code
from pyagnostics.spans import LabeledSpan, SourceSpan


def fail() -> None:
    try:
        try:
            1 / 0
        except Exception as e:
            raise DiagnosticError(
                severity=Severity.ERROR,
                code="pyagnostics::test",
                message="inner",
                notes=["This is a note"],
            ) from e
    except Exception:
        raise RuntimeError("the cause\nof the error")


def main() -> None:
    try:
        with attach_diagnostic_source_code(InMemorySource("1 + 1 = 2")):
            try:
                fail()
            except Exception as e:
                raise DiagnosticError(
                    severity=Severity.ERROR,
                    code="pyagnostics::test",
                    message="Some error occurred",
                    labels=[LabeledSpan(SourceSpan(4, 5), "this")],
                    notes=[
                        "[blue]help:[/blue] You did something dumb",
                        "[green]did you mean:[/green] 1 + 3",
                    ],
                ) from e
    except DiagnosticError as e:
        from rich import print

        print(e.with_context("while testing"))


if __name__ == "__main__":
    main()

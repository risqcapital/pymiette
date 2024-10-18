from enum import StrEnum, auto
from typing import Self

from rich.style import Style


class Severity(StrEnum):
    ADVICE = auto()
    WARNING = auto()
    ERROR = auto()

    @property
    def style(self: Self) -> Style:
        match self:
            case Severity.ADVICE:
                return Style(color="blue")
            case Severity.WARNING:
                return Style(color="yellow")
            case Severity.ERROR:
                return Style(color="red")
            case _:
                raise ValueError(f"Unknown severity: {self!r}")

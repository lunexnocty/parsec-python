from typing import Optional


class ParseErr(Exception): ...


class Expected[R](ParseErr):
    def __init__(self, value: R, children: Optional[list[ParseErr]] = None):
        self.value = value
        self.children = children or []


class UnExpected[R](ParseErr):
    def __init__(self, value: R, expected: Optional[ParseErr] = None):
        self.value = value
        self.expected = expected


class InvalidValue[R](ParseErr):
    def __init__(self, value: R, expected: Optional[ParseErr] = None):
        self.value = value
        self.expected = expected


class EOS(ParseErr):
    def __init__(self) -> None: ...


class AlterErr(ParseErr):
    def __init__(self, children: list[ParseErr]):
        self.children = children

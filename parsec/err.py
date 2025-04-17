from typing import Optional


class ParseErr:
    def __init__(self, children: Optional[list["ParseErr"]] = None):
        self.children = children or []

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({'' if hasattr(self, 'value') else f'value={getattr(self, "value")}'}, children={self.children})>"


class Expected[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value


class UnExpected[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value


class InvalidValue[R](ParseErr):
    def __init__(self, value: R):
        super().__init__()
        self.value = value


class EOSError(ParseErr):
    def __init__(self) -> None:
        super().__init__()

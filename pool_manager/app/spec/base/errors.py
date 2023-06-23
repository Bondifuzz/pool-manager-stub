class SpecError(Exception):
    """Base exception. Never raised directly"""


class SpecLoadError(SpecError):

    """Raised when specification load failed"""

    def __init__(self, filepath: str) -> None:
        super().__init__(f"Failed to load specification file '{filepath}'")


class SpecValidationError(SpecError):

    """Raised when specification contains null entries"""

    def __init__(self, key: str) -> None:
        super().__init__(key)

    @property
    def key(self):
        return self.args[0]

    def __str__(self) -> str:
        return f"Undefined value was found in key: '{self.key}'"


class SpecParseError(SpecError):

    """Raised when failed to parse specification"""

    def __init__(self, key: str, reason: str) -> None:
        super().__init__(key, reason)

    @property
    def key(self):
        return self.args[0]

    @property
    def reason(self):
        return self.args[1]

    def __str__(self) -> str:
        return f"Parse error: {self.reason}. Key: '{self.key}'"


class UsageError(SpecError):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Usage error - {msg}")

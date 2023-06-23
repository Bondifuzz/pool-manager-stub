from ..base.errors import SpecError


class PoolSpecError(SpecError):
    pass


class PoolSpecLoadError(PoolSpecError):
    pass


class PoolSpecValidationError(PoolSpecError):
    def __init__(self, msg: str) -> None:
        err = "Validation of pool specification failed"
        super().__init__(f"{err}. {msg}")


class PoolSpecParseError(PoolSpecError):
    def __init__(self, msg: str) -> None:
        err = "Failed to parse pool specification"
        super().__init__(f"{err}. {msg}")

from dataclasses import dataclass


@dataclass
class HapeError(Exception):
    code: str
    message: str
    exit_code: int = 1
    context: dict[str, str] | None = None

    def __post_init__(self) -> None:
        super().__init__(self.message)


class HapeValidationError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 2, context: dict[str, str] | None = None) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code, context=context)


class HapeOperationError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 3, context: dict[str, str] | None = None) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code, context=context)


class HapeExternalError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 3, context: dict[str, str] | None = None) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code, context=context)


class HapeUserAbortError(HapeError):
    def __init__(self, code: str, message: str, exit_code: int = 130, context: dict[str, str] | None = None) -> None:
        super().__init__(code=code, message=message, exit_code=exit_code, context=context)


if __name__ == "__main__":
    print(HapeValidationError(code="HAPE_EXAMPLE", message="Example validation error."))

from typing import Callable, Optional

from core.errors.exceptions import HapeError
from core.logging import LocalLogging


class ErrorHandler:
    DEFAULT_UNKNOWN_EXIT_CODE = 99
    DEFAULT_UNKNOWN_MESSAGE = "Unexpected error. Please check logs and rerun."

    @staticmethod
    def handle(exc: Exception, print_fn: Optional[Callable[[str], None]] = None) -> int:
        LocalLogging.bootstrap()
        active_logger = LocalLogging.get_logger("hape.error_handler")
        active_print = print_fn or print

        if isinstance(exc, HapeError):
            if exc.context:
                active_logger.error(f"[{exc.code}] {exc.message} | context={exc.context}")
            else:
                active_logger.error(f"[{exc.code}] {exc.message}")
            active_print(f"Error: {exc.message}")
            return exc.exit_code

        active_logger.error(f"[HAPE_UNKNOWN_ERROR] {exc.__class__.__name__}: {exc}")
        active_print(f"Error: {ErrorHandler.DEFAULT_UNKNOWN_MESSAGE}")
        return ErrorHandler.DEFAULT_UNKNOWN_EXIT_CODE


if __name__ == "__main__":
    exit_code = ErrorHandler.handle(Exception("example"))
    print(f"example-exit-code={exit_code}")

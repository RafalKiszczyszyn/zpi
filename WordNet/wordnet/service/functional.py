from __future__ import annotations

from collections import Iterable
from dataclasses import dataclass
from typing import Any, Callable, Union


@dataclass
class Error:
    message: str
    isRuntime: bool = True
    exception: Union[Exception, None] = None


@dataclass(frozen=True)
class Result:
    value: Union[Any, None]
    error: Union[Error, None]

    @property
    def isSuccess(self) -> bool:
        return self.error is None

    def then(self, func: Callable[[Any], Result]) -> Result:
        if not self.isSuccess:
            return self
        if type(self.value) in [list, tuple]:
            return func(*self.value)
        return func(self.value)

    @staticmethod
    def success(value: Any) -> Result:
        return Result(value=value, error=None)

    @staticmethod
    def failure(error: Error) -> Result:
        return Result(value=None, error=error)

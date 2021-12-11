from contextlib import contextmanager
from typing import Any, Tuple
from unittest import mock


@contextmanager
def mockProperty(target: str, value: Any) -> Tuple[mock.Mock, mock.PropertyMock]:
    _mock = mock.Mock()
    propertyMock = mock.PropertyMock()
    propertyMock.return_value = value
    setattr(type(_mock), target, propertyMock)
    yield _mock, propertyMock
    delattr(type(_mock), target)

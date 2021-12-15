import importlib
from abc import ABC, abstractmethod
from inspect import signature

from feedreader.core import config, exceptions


class ICallableInvoker(ABC):
    """Interface like abstract class to indicate Invoker implementations."""

    @abstractmethod
    def invoke(self, __callable__: callable, *args, **kwargs):
        pass


class CallableInvoker(ICallableInvoker):

    @classmethod
    def invoke(cls, __callable__: callable, *args, **kwargs):
        if not callable(__callable__):
            raise TypeError(f"'{__callable__}' is not callable")

        if not CallableInvoker._has_args_and_kwargs(__callable__):
            raise exceptions.MissingParameter(__callable__, '*args', '**kwargs')

        return __callable__(*args, **kwargs)

    @staticmethod
    def _has_args_and_kwargs(__callable__):
        # TODO: Consider better way of checking if method has args and kwargs
        params = signature(__callable__).parameters
        count = 0
        for param_name in params:
            if str(params[param_name]).startswith('*') or str(params[param_name]).startswith('**'):
                count += 1

        return count == 2


class IClassLoader(ABC):
    """Interface like abstract class to indicate ClassLoader implementations."""

    @abstractmethod
    def load(self, full_class_name: str, *args, **kwargs):
        pass


class ClassLoader(IClassLoader):

    def __init__(self, invoker: ICallableInvoker):
        self.invoker = invoker

    def load(self, full_class_name: str, *args, **kwargs):
        if type(full_class_name) != str:
            raise exceptions.NotAnInstance(full_class_name, str)

        if '.' not in full_class_name:
            raise exceptions.InvalidParameter(full_class_name, 'must be a full class name')

        module_name, class_name = full_class_name.rsplit('.', maxsplit=1)
        module = importlib.import_module(module_name)

        if not hasattr(module, class_name):
            raise ImportError(f"Class='{class_name}' does not exits in '{module}'")

        class_ = getattr(module, class_name)
        instance = self.invoker.invoke(class_, *args, **kwargs)

        return instance


class IImplementationBuilder(ABC):
    """Interface like abstract class to indicate ImplementationBuilder implementations."""

    @abstractmethod
    def build(self, _class: config.ClassConfig, *args, **kwargs):
        pass


class ImplementationBuilder(IImplementationBuilder):

    def __init__(self, class_loader: IClassLoader):
        self.class_loader = class_loader

    def build(self, _class: config.ClassConfig, *args, **kwargs):
        if not issubclass(type(_class), config.ClassConfig):
            raise exceptions.NotASubclass(_class, config.ClassConfig)

        implementation = self.class_loader.load(_class.implementation, *args, **kwargs, **_class.args)
        return implementation


def implementation_builder_factory():
    invoker = CallableInvoker()
    class_loader = ClassLoader(invoker)
    return ImplementationBuilder(class_loader)


def kwarg_lookup(kwargs: dict, name: str, required=False):
    if name in kwargs:
        return kwargs[name]

    if required:
        raise KeyError(f"Kwarg='{name}' is required")

    return None

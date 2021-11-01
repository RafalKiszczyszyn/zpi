import importlib
from abc import ABC, abstractmethod
from inspect import signature, isclass


class AbstractInvoker(ABC):
    """Interface like abstract class to indicate Invoker implementations."""

    @abstractmethod
    def invoke(self, __method__: callable, *args, **kwargs):
        pass


class Invoker(AbstractInvoker):

    @classmethod
    def invoke(cls, __method__: callable, *args, **kwargs):
        if not callable(__method__):
            raise Exception(f'{__method__} is not callable.')

        if not Invoker._has_args_and_kwargs(__method__):
            raise Exception(f'Method {__method__} must take *args and **kwargs parameters.')

        return __method__(*args, **kwargs)

    @staticmethod
    def _has_args_and_kwargs(method):
        # TODO: Consider better way of checking if method has args and kwargs
        params = signature(method).parameters
        count = 0
        for param_name in params:
            if str(params[param_name]).startswith('*') or str(params[param_name]).startswith('**'):
                count += 1

        return count == 2


class AbstractClassLoader(ABC):
    """Interface like abstract class to indicate ClassLoader implementations."""

    @abstractmethod
    def load(self, full_class_name: str, *args, **kwargs):
        pass


class ClassLoader(AbstractClassLoader):

    def __init__(self, invoker: AbstractInvoker):
        if not issubclass(type(invoker), AbstractInvoker):
            raise TypeError('Parameter invoker must be an implementation of AbstractInvoker.')
        self.invoker = invoker

    def load(self, full_class_name: str, *args, **kwargs):
        if type(full_class_name) != str:
            raise TypeError(f'Parameter full_class_name must be a str.')

        if '.' not in full_class_name:
            raise Exception(f"{full_class_name} must be a full class name.")

        module_name, class_name = full_class_name.rsplit('.', maxsplit=1)
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise Exception(f"Module specified in {full_class_name} does not exist.")

        if not hasattr(module, class_name):
            raise Exception(f"Class {class_name} does not exits in {module}.")

        class_ = getattr(module, class_name)

        try:
            instance = self.invoker.invoke(class_, *args, **kwargs)
        except Exception as e:
            raise Exception(f"Failed to load {class_} with message: {e}.")

        if not isclass(type(instance)):
            raise Exception(f'{class_} is not a class.')
        return instance


class AbstractImplementationBuilder(ABC):
    """Interface like abstract class to indicate ImplementationBuilder implementations."""

    @abstractmethod
    def build(self, config, *args, **kwargs):
        pass


class ImplementationBuilder(AbstractImplementationBuilder):

    def __init__(self, class_loader: AbstractClassLoader):
        if not issubclass(type(class_loader), AbstractClassLoader):
            raise TypeError('Parameter class_loader must be an implementation of AbstractClassLoader.')
        self.class_loader = class_loader

    def build(self, config, *args, **kwargs):
        if 'class' not in config:
            raise Exception('No implementation class name specified.')

        full_class_name = config['class']
        config_args = {}
        if 'args' in config:
            config_args = config['args']

        try:
            implementation = self.class_loader.load(full_class_name, *args, **kwargs, **config_args)
            return implementation
        except Exception as e:
            raise Exception(f'Loading implementation failed with message: {e}')


def implementation_builder_factory():
    invoker = Invoker()
    class_loader = ClassLoader(invoker)
    return ImplementationBuilder(class_loader)


def kwarg_lookup(kwargs: dict, name: str, required=False):
    if name in kwargs:
        return kwargs[name]

    if required:
        raise Exception(f"Kwarg='{name}' is required.")

    return None

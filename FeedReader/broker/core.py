import importlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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


@dataclass
class InjectService:
    service_name: str
    attribute_name: str


@dataclass
class ConfigArgs:
    required: [str]
    optional: [str] = field(default_factory=list)
    validate: bool = False


class AbstractMetaResolver(ABC):
    """Interface like abstract class to indicate Meta Resolver implementations."""

    @abstractmethod
    def resolve(self, instance, args=None):
        pass


class MetaResolver(AbstractMetaResolver):

    def __init__(self, services, on_injection_failure=None):
        self.services = services
        self.on_injection_failure = on_injection_failure

    def resolve(self, instance, args=None):
        if not args:
            args = {}

        mro = type.mro(type(instance))
        for class_ in filter(lambda c: hasattr(c, 'Meta') and isclass(c.Meta), mro):
            self._apply_meta(instance, class_.Meta, args)

    def _apply_meta(self, instance, meta, args):
        if hasattr(meta, 'services'):
            self._inject_services(instance, meta.services)

        if hasattr(meta, 'args'):
            MetaResolver._parse_args(instance, meta.args, args)
        pass

    def _inject_services(self, instance: object, meta_services: [InjectService]):
        if [meta_services for meta_service in meta_services if not isinstance(meta_service, InjectService)]:
            raise Exception(f"{instance.Meta}.services must be a list of InjectService.")

        for meta_service in meta_services:
            if meta_service.service_name in self.services:
                setattr(instance, meta_service.attribute_name, self.services[meta_service.service_name])
            elif self.on_injection_failure:
                self.on_injection_failure(meta_service)
                # print(f'WARNING: Service={meta_service.service_name} not found in config file. '
                #       'Thus will not be injected.')

        pass

    @staticmethod
    def _parse_args(instance: object, meta_args: ConfigArgs, args: dict):
        if not isinstance(meta_args, ConfigArgs):
            raise Exception(f'{instance.Meta}.args must be a ConfigArgs.')

        for req_attr in meta_args.required:
            if req_attr not in args:
                raise Exception(f'Required attribute \'{req_attr}\' was not given for {type(instance)}.')
            setattr(instance, req_attr, args[req_attr])

        for opt_attr in meta_args.optional:
            if opt_attr in args:
                setattr(instance, opt_attr, args[opt_attr])

        if meta_args.validate:
            if not (hasattr(instance, 'validate_config_args')
                    and MetaResolver._is_validation_method(instance.validate_config_args)):
                raise Exception(f'{type(instance)} does not have validate_config_args method '
                                f'that takes 0 arguments, required to validate args.')
            instance.validate_config_args()
        pass

    @staticmethod
    def _is_validation_method(__method__):
        if not callable(__method__):
            return False

        params = signature(__method__).parameters
        if len(params) == 0:
            return True

        pos_args = [param for param in params if not str(params[param]).startswith('*')]

        return len(pos_args) == 0


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

    def __init__(self, class_loader: AbstractClassLoader, meta_resolver: AbstractMetaResolver):
        if not issubclass(type(class_loader), AbstractClassLoader):
            raise TypeError('Parameter class_loader must be an implementation of AbstractClassLoader.')
        if not issubclass(type(meta_resolver), AbstractMetaResolver):
            raise TypeError('Parameter meta_resolver must be an implementation of AbstractMetaResolver.')
        self.class_loader = class_loader
        self.meta_resolver = meta_resolver

    def build(self, config, *args, **kwargs):
        if 'class' not in config:
            raise Exception('No implementation class name specified.')

        full_class_name = config['class']
        config_args = {}
        if 'args' in config:
            config_args = config['args']

        try:
            implementation = self.class_loader.load(full_class_name, *args, **kwargs)
            self.meta_resolver.resolve(implementation, config_args)
            return implementation
        except Exception as e:
            raise Exception(f'Loading implementation failed with message: {e}')


def implementation_builder_factory(services):
    invoker = Invoker()
    meta_resolver = MetaResolver(services)
    class_loader = ClassLoader(invoker)
    return ImplementationBuilder(class_loader, meta_resolver)

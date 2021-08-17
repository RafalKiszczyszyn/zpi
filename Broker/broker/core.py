import importlib
import inspect

from broker import endpoints, config, logging, interceptors as inters
from broker.logging import log_exception


class Task:

    def __init__(self,
                 source: endpoints.SourceEndpointBase,
                 destination: endpoints.DestinationEndpointBase,
                 interceptors=None):
        self.__source = source
        self.__destination = destination
        self.__interceptors = interceptors

    @log_exception
    def execute(self):
        content = self.__source.pull()
        if self.__interceptors:
            content = self.transform_content(content)
        self.__destination.push(content)

    def transform_content(self, content):
        for interceptor in self.__interceptors:
            content = interceptor.transform(content)
        return content


class TaskBuilderException(Exception):
    pass


class TaskBuilder:

    def __init__(self, tasks):
        self.__tasks = tasks

    def build(self):
        tasks = []
        for _task in self.__tasks:
            try:
                source_endpoint = self.__build_source_endpoint(_task['source'])
                destination_endpoint = self.__build_destination_endpoint(_task['destination'])

                interceptors = None
                if 'interceptors' in _task:
                    interceptors = self.__build_interceptors(_task['interceptors'])

                tasks.append(Task(source_endpoint, destination_endpoint, interceptors))
            except KeyError as e:
                raise TaskBuilderException(f"{e} not found in config file.")

        return tasks

    def __build_source_endpoint(self, _source):
        endpoint, source_class_name = self.__build_endpoint(_source)
        if not issubclass(type(endpoint), endpoints.SourceEndpointBase):
            raise TaskBuilderException(f"{source_class_name} class is not subclass of endpoints.SourceEndpointBase")

        return endpoint

    def __build_destination_endpoint(self, _source):
        endpoint, source_class_name = self.__build_endpoint(_source)
        if not issubclass(type(endpoint), endpoints.DestinationEndpointBase):
            raise TaskBuilderException(
                f"{source_class_name} class is not subclass of endpoints.DestinationEndpointBase")

        return endpoint

    @staticmethod
    def __build_interceptors(_interceptors):
        interceptors = []
        for _interceptor in _interceptors:
            interceptor = ClassLoader.load(_interceptor)

            if not issubclass(type(interceptor), inters.InterceptorBase):
                raise TaskBuilderException(f"{_interceptor} class is not subclass of interceptors.InterceptorBase")

            interceptors.append(interceptor)

        return interceptors

    @staticmethod
    def __build_endpoint(_endpoint):
        source_class_name = _endpoint['class']
        args = _endpoint['args']

        endpoint = ClassLoader.load(source_class_name, _endpoint, **args)

        if endpoint is None:
            raise TaskBuilderException(f"Could not load {source_class_name} class.")

        if not issubclass(type(endpoint), endpoints.EndpointBase):
            raise TaskBuilderException(f"{source_class_name} class is not subclass of endpoints.EndpointBase")

        return endpoint, source_class_name


class ClassLoaderException(Exception):
    pass


class ClassLoader:

    @staticmethod
    def load(full_class_name, *args, **kwargs):
        module_name, class_name = ClassLoader.__get_module_name_and_class_name(full_class_name)
        module = importlib.import_module(module_name)

        if hasattr(module, class_name):
            _class = getattr(module, class_name)
            return ClassLoader.init_class(_class, *args, **kwargs)
        else:
            return None

    @staticmethod
    def __get_module_name_and_class_name(full_class_name: str):
        return full_class_name.rsplit('.', maxsplit=1)

    @staticmethod
    def init_class(_class, *args, **kwargs):
        try:
            return _class(*args, **kwargs) \
                if inspect.isclass(_class) \
                else None
        except Exception as e:
            raise ClassLoaderException(f"Failed to load class with message: {e}")


def execute(tasks):
    for task in tasks:
        task.execute()


def get_tasks_from_config():
    try:
        return TaskBuilder(config.TASKS).build()
    except Exception as e:
        print(e)
        exit(-1)


def startup():
    if hasattr(config, 'LOGGER'):
        logger = ClassLoader.load(config.LOGGER)
        if issubclass(type(logger), logging.LoggerBase):
            logging.logger = logger

    tasks = []
    if hasattr(config, 'TASKS'):
        tasks = get_tasks_from_config()
    else:
        print("No tasks in config file.")

    execute(tasks)

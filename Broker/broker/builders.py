from broker.core import AbstractMetaResolver, AbstractImplementationBuilder
from broker.tasks import TaskStepBase, Task


class ServiceBuilder:

    def __init__(self, implementation_builder: AbstractImplementationBuilder):
        if not issubclass(type(implementation_builder), AbstractImplementationBuilder):
            raise TypeError('Parameter implementation_builder '
                            'must be an implementation of AbstractImplementationBuilder.')
        self.implementation_builder = implementation_builder

    def build(self, config):
        services = {}
        for service_name in config:
            implementation = self.implementation_builder.build(config[service_name])
            services[service_name] = implementation
        return services


class TaskBuilder:

    def __init__(self, implementation_builder: AbstractImplementationBuilder, meta_resolver: AbstractMetaResolver):
        if not issubclass(type(implementation_builder), AbstractImplementationBuilder):
            raise TypeError('Parameter implementation_builder '
                            'must be an implementation of AbstractImplementationBuilder.')
        if not issubclass(type(meta_resolver), AbstractMetaResolver):
            raise TypeError('Parameter meta_resolver must be an implementation of AbstractMetaResolver.')
        self.implementation_builder = implementation_builder
        self.meta_resolver = meta_resolver

    def build(self, config):
        if 'name' not in config:
            raise Exception('No task name specified.')
        if 'steps' not in config:
            raise Exception('No task steps specified.')

        context = f'Task={config["name"]}'
        steps = []
        try:
            for config_step in config['steps']:
                step = self._build_task_step(config_step, context)
                steps.append(step)
        except Exception as e:
            raise Exception(f'Loading task step failed with message: {e}')

        task = Task(context, steps)
        self.meta_resolver.resolve(task, {})
        return task

    def _build_task_step(self, config, context):
        if 'name' not in config:
            raise Exception('No task step name specified.')

        context = f'{context}, Step={config["name"]}'
        try:
            implementation = self.implementation_builder.build(config, context=context)
            if not issubclass(type(implementation), TaskStepBase):
                raise Exception('Task step implementation must be a subclass of TaskStepBase.')
            return implementation
        except Exception as e:
            raise Exception(f'Loading task step implementation failed with message: {e}')

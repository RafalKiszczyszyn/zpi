from __future__ import annotations

import json
from abc import abstractmethod, ABC
from typing import List, Dict, Tuple, Any

from feedreader.core import loading, config, exceptions


class ITaskBuilder(ABC):

    @abstractmethod
    def build(self, task: config.TaskConfig):
        pass


class TaskBuilder(ITaskBuilder):

    def __init__(self, implementation_builder: loading.IImplementationBuilder):
        if not issubclass(type(implementation_builder), loading.IImplementationBuilder):
            raise exceptions.NotASubclass(implementation_builder, loading.IImplementationBuilder)

        self.implementation_builder = implementation_builder

    def build(self, task: config.TaskConfig):
<<<<<<< HEAD
        if not isinstance(task, config.TaskConfig):
=======
        if isinstance(task, type(config.TaskConfig)):
>>>>>>> 9d1372c7bc15b97a1c7151c5452c237f88491ecf
            raise exceptions.NotAnInstance(task, config.TaskConfig)

        context = f"Task='{task.name}'"
        steps = []
        for step in task.steps:
            step = self._build_task_step(step, context)
            steps.append(step)

        task = Task(context, steps)
        return task

    def _build_task_step(self, step: config.StepConfig, context):
<<<<<<< HEAD
=======
        if type(step) is not config.StepConfig:
            raise exceptions.NotAnInstance(step, config.StepConfig)

>>>>>>> 9d1372c7bc15b97a1c7151c5452c237f88491ecf
        context = f"{context}, Step='{step.name}'"
        implementation = self.implementation_builder.build(step, context=context)
        if not issubclass(type(implementation), ITaskStep):
            raise exceptions.NotASubclass(implementation, ITaskStep)

        return implementation


class ITaskExecutorProvider(ABC):

    @abstractmethod
    def loadFromJsonFile(self, executor: config.ClassConfig, tasks: List[config.TaskConfig]) -> ITaskExecutor:
        pass


class TaskExecutorProvider(ITaskExecutorProvider):

<<<<<<< HEAD
    def __init__(self, impl_builder: loading.IImplementationBuilder, task_builder: ITaskBuilder):
        if not issubclass(type(impl_builder), loading.IImplementationBuilder):
            raise exceptions.NotASubclass(impl_builder, loading.IImplementationBuilder)
        if not issubclass(type(task_builder), ITaskBuilder):
            raise exceptions.NotASubclass(task_builder, ITaskBuilder)
=======
    def __init__(self, impl_builder: loading.IImplementationBuilder, task_builder: TaskBuilder):
        if not issubclass(type(impl_builder), loading.IImplementationBuilder):
            raise exceptions.NotASubclass(impl_builder, loading.IImplementationBuilder)
        if not issubclass(type(task_builder), TaskBuilder):
            raise exceptions.NotASubclass(task_builder, TaskBuilder)
>>>>>>> 9d1372c7bc15b97a1c7151c5452c237f88491ecf

        self._impl_builder = impl_builder
        self._task_builder = task_builder

    def loadFromJsonFile(self, executor: config.ClassConfig, fileName: str) -> ITaskExecutor:
        mapper = config.TaskConfigMapper()

        with open(fileName, 'r') as file:
            taskConfigs_ = json.load(file)

        tasks = []
        for taskConfig_ in taskConfigs_:
            taskConfig = mapper.fromDict(taskConfig_)
            task = self._task_builder.build(taskConfig)
            tasks.append(task)

        return self._impl_builder.build(executor, tasks=tasks)


class ITask(ABC):

    @property
    @abstractmethod
    def context(self) -> str:
        pass

    @abstractmethod
    def execute(self) -> dict:
        pass


class Task(ITask):

    def __init__(self, context, steps):
        self._context = context
        self._steps = steps

    @property
    def context(self) -> str:
        return self._context

    def execute(self) -> dict:
        data = {}
        for step in self._steps:
            data = step.execute(data)
        return data


class ITaskExecutor(ABC):

    @property
    @abstractmethod
    def tasks_count(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class TaskExecutorBase(ITaskExecutor, ABC):

    def __init__(self, tasks: List[ITask]):
        self._tasks = tasks

    @property
    def tasks_count(self):
        return len(self._tasks)

    @abstractmethod
    def before(self):
        pass

    @abstractmethod
    def before_each(self, context):
        pass

    def execute(self):
        self.before()

        results: List[Tuple[str, dict]] = []
        for task in self._tasks:
            self.before_each(task.context)
            result: dict = {}
            try:
                result = task.execute()
                results.append((task.context, result))
            except Exception as e:
                self.handle_exception(task.context, e)
            self.after_each(task.context, result)
        self.after(results)

    @abstractmethod
    def handle_exception(self, context: str, e: Exception):
        pass

    @abstractmethod
    def after_each(self, context: str, result):
        pass

    @abstractmethod
    def after(self, results):
        pass


class ITaskStep(ABC):

    @property
    @abstractmethod
    def context(self) -> str:
        pass

    @abstractmethod
    def execute(self, data):
        pass


def task_executor_provider_factory():
    impl_builder = loading.implementation_builder_factory()
    return TaskExecutorProvider(impl_builder, TaskBuilder(impl_builder))

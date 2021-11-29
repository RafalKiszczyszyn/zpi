from __future__ import annotations
from abc import abstractmethod, ABC
from typing import List, Tuple

from feedreader.core import core, config, exceptions


class ITaskBuilder(ABC):

    @abstractmethod
    def build(self, task: config.Task):
        pass


class TaskBuilder(ITaskBuilder):

    def __init__(self, implementation_builder: core.IImplementationBuilder):
        if not issubclass(type(implementation_builder), core.IImplementationBuilder):
            raise exceptions.NotASubclass(implementation_builder, core.IImplementationBuilder)

        self.implementation_builder = implementation_builder

    def build(self, task: config.Task):
        if isinstance(task, type(config.Task)):
            raise exceptions.NotAnInstance(task, config.Task)

        context = f"Task='{task.name}'"
        steps = []
        for step in task.steps:
            step = self._build_task_step(step, context)
            steps.append(step)

        task = Task(context, steps)
        return task

    def _build_task_step(self, step: config.Step, context):
        if type(step) is not config.Step:
            raise exceptions.NotAnInstance(step, config.Step)

        context = f"{context}, Step='{step.name}'"
        implementation = self.implementation_builder.build(step, context=context)
        if not issubclass(type(implementation), ITaskStep):
            raise exceptions.NotASubclass(implementation, ITaskStep)

        return implementation


class ITaskExecutorProvider(ABC):

    @abstractmethod
    def load_from_config(self, executor: config.Class, tasks: List[config.Task]) -> ITaskExecutor:
        pass


class TaskExecutorProvider(ITaskExecutorProvider):

    def __init__(self, impl_builder: core.IImplementationBuilder, task_builder: TaskBuilder):
        if not issubclass(type(impl_builder), core.IImplementationBuilder):
            raise exceptions.NotASubclass(impl_builder, core.IImplementationBuilder)
        if not issubclass(type(task_builder), TaskBuilder):
            raise exceptions.NotASubclass(task_builder, TaskBuilder)

        self._impl_builder = impl_builder
        self._task_builder = task_builder

    def load_from_config(self, executor: config.Class, tasks: List[config.Task]) -> ITaskExecutor:
        tasks_ = []
        for task in tasks:
            task = self._task_builder.build(task)
            tasks_.append(task)

        return self._impl_builder.build(executor, tasks=tasks_)


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
    impl_builder = core.implementation_builder_factory()
    return TaskExecutorProvider(impl_builder, TaskBuilder(impl_builder))

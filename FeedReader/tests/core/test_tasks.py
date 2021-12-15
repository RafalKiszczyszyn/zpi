import os
import pathlib
from dataclasses import dataclass, field
from unittest.mock import patch
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from feedreader.core import loading, config

from feedreader.core.exceptions import NotASubclass, NotAnInstance

from feedreader.core.tasks import TaskBuilder, ITaskStep, TaskExecutorProvider, ITaskBuilder, TaskExecutorBase, \
    task_executor_provider_factory, ITaskExecutorProvider

from unittest import TestCase, mock


@dataclass(frozen=True)
class ImplementationBuilderMock(loading.IImplementationBuilder):
    build: mock.Mock = field(default_factory=lambda: mock.Mock())


@dataclass(frozen=True)
class TaskStepMock(ITaskStep):
    context = mock.Mock()
    execute: mock.Mock = field(default_factory=lambda: mock.Mock())


@dataclass(frozen=True)
class TaskBuilderMock(ITaskBuilder):
    build: mock.Mock = field(default_factory=lambda: mock.Mock())


class TaskBuilderTests(TestCase):

    def test_Init_InvalidType_NotASubclassIsRaised(self):
        # Act + Assert
        self.assertRaises(NotASubclass, TaskBuilder, 'InvalidType')

    def test_Build_InvalidType_NotAnInstanceIsRaised(self):
        # Act + Assert
        self.assertRaises(
            NotAnInstance,
            TaskBuilder(ImplementationBuilderMock()).build, 'InvalidType')

    def test_Build_ImplementationHasInvalidType_NotASubclassIsRaised(self):
        # Arrange
        implBuilderMock = ImplementationBuilderMock()
        implBuilderMock.build.return_value = 'Invalid Type'
        taskConfig = config.TaskConfig(name='TaskName', steps=[
            config.StepConfig(name='StepName', implementation='module.ClassName')
        ])

        # Act + Assert
        self.assertRaises(
            NotASubclass,
            TaskBuilder(implBuilderMock).build, taskConfig)

    def test_Build_ValidTaskConfig_TaskIsReturned(self):
        # Arrange
        implBuilderMock = ImplementationBuilderMock()
        taskStepMock = TaskStepMock()
        implBuilderMock.build.return_value = taskStepMock
        taskConfig = config.TaskConfig(name='TaskName', steps=[
            config.StepConfig(name='StepName', implementation='module.ClassName')
        ])

        # Act
        task = TaskBuilder(implBuilderMock).build(taskConfig)
        task.execute()

        # Assert
        taskStepMock.execute.assert_called_once_with({})
        self.assertTrue(True)


class TaskExecutorProviderTests(TestCase):

    def test_Init_InvalidType_NotASubclassIsRaised(self):
        # Act + Assert
        self.assertRaises(NotASubclass, TaskExecutorProvider, 'InvalidType', 'InvalidType')
        self.assertRaises(NotASubclass, TaskExecutorProvider, ImplementationBuilderMock(), 'InvalidType')

    @patch('json.load')
    @patch('feedreader.core.config.TaskConfigMapper')
    def test_LoadFromJsonFile_ConfigIsValid_TaskExecutorIsReturned(self, mapperMock, jsonMock):
        # Arrange
        open('sources.json', 'w').close()

        jsonMock.return_value = [1]

        implBuilderMock = ImplementationBuilderMock()
        taskBuilderMock = TaskBuilderMock()

        # Act
        TaskExecutorProvider(implBuilderMock, taskBuilderMock).loadFromJsonFile(
            config.ClassConfig(implementation='module.ClassName'), 'sources.json')

        # Assert
        mapperMock().fromDict.assert_called_once()
        implBuilderMock.build.assert_called_once()
        taskBuilderMock.build.assert_called_once()
        self.assertTrue(True)

        os.remove('sources.json')


class TaskExecutorBaseTests(TestCase):

    class ImplMock(TaskExecutorBase):
        before = mock.Mock()
        before_each = mock.Mock()
        handle_exception = mock.Mock()
        after_each = mock.Mock()
        after = mock.Mock()

    def _raise(*args, **kwargs):
        raise Exception()

    def test_Execute_SomeTaskFailed_FailuresAreSkipped(self):
        # Arrange
        succeededTaskMock = mock.Mock()
        succeededTaskMock.context = 'Context'
        succeededTaskMock.execute.return_value = 'Value'
        failedTaskMock = mock.Mock()
        failedTaskMock.execute = self._raise
        sut = self.ImplMock(tasks=[failedTaskMock, succeededTaskMock])

        # Act
        sut.execute()

        # Assert
        sut.before.assert_called_once()
        self.assertEqual(sut.before_each.call_count, 2)
        sut.handle_exception.assert_called_once()
        self.assertEqual(sut.after_each.call_count, 2)
        sut.after.assert_called_once_with([('Context', 'Value')])


class ModuleTests(TestCase):

    def test_TaskExecutorProviderFactory_ProviderIsReturned(self):
        # Act
        provider = task_executor_provider_factory()

        # Assert
        self.assertTrue(issubclass(type(provider), ITaskExecutorProvider))

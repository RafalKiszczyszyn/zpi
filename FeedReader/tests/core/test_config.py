import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

from feedreader.core.config import TaskConfig, StepConfig, TaskConfigMapper
from unittest import TestCase


class TaskConfigMapperTests(TestCase):

    def test_ToDict_TaskConfigWithManySteps_AllIsMappedToDict(self):
        # Arrange
        taskConfig = TaskConfig(name='TaskName', steps=[
            StepConfig(name='Step1', implementation='implementation1', args=None),
            StepConfig(name='Step2', implementation='implementation2', args={'arg': 'value'})
        ])

        # Act
        dict_ = TaskConfigMapper().toDict(taskConfig)

        # Assert
        self.assertMappingIsValid(dict_, taskConfig)

    def test_FromDict_TaskDictDoesNotContainNameKey_KeyErrorIsRaised(self):
        # Arrange
        dict_ = {}

        # Act + Assert
        self.assertRaises(KeyError, TaskConfigMapper().fromDict, dict_)

    def test_FromDict_TaskDictDoesNotContainStepsKey_KeyErrorIsRaised(self):
        # Arrange
        dict_ = {'name': 'TaskName'}

        # Act + Assert
        self.assertRaises(KeyError, TaskConfigMapper().fromDict, dict_)

    def test_FromDict_TaskStepDictDoesNotContainRequiredKey_KeyErrorIsRaise(self):
        # Arrange
        dict_ = {
            "name": "TaskName",
            "steps": [{
                "name": "StepName"
            }]}

        # Act + Assert
        self.assertRaises(KeyError, TaskConfigMapper().fromDict, dict_)

    def test_FromDict_TaskDictIsComplete_TaskConfigIsReturned(self):
        # Arrange
        dict_ = {
            "name": "TaskName",
            "steps": [{
                "name": "StepName",
                "implementation": "Implementation",
                "args": {"arg": "value"}
            }]}

        # Act
        taskConfig = TaskConfigMapper().fromDict(dict_)

        # Assert
        self.assertMappingIsValid(dict_, taskConfig)

    def assertMappingIsValid(self, taskDict, taskConfig):
        self.assertEqual(taskDict['name'], taskConfig.name)
        for stepConfig, mapped in zip(taskConfig.steps, taskDict['steps']):
            self.assertEqual(mapped['name'], stepConfig.name)
            self.assertEqual(mapped['implementation'], stepConfig.implementation)
            self.assertEqual(mapped['args'], stepConfig.args)
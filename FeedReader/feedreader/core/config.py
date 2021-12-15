from dataclasses import dataclass
from typing import List, Dict, Any


class ClassConfig:

    def __init__(self, implementation: str, args: dict = None):
        self.implementation = implementation
        self.args = args if args else {}


class StepConfig(ClassConfig):

    def __init__(self, name: str, implementation: str, args: dict = None):
        super().__init__(implementation, args)
        self.name = name


@dataclass
class TaskConfig:
    name: str
    steps: List[StepConfig]


class TaskConfigMapper:

    @classmethod
    def fromDict(cls, task_: Dict[str, Any]):
        if 'name' not in task_:
            raise KeyError("Task must have name specified")
        if 'steps' not in task_:
            raise KeyError("Task must have steps specified")

        steps = []
        for step_ in task_['steps']:
            try:
                step = StepConfig(
                    name=step_['name'],
                    implementation=step_['implementation'],
                    args=step_['args'] if 'args' in step_ else {})
                steps.append(step)
            except KeyError as e:
                raise KeyError(f'Task step must have {e} specified')

        return TaskConfig(name=task_['name'], steps=steps)

    @classmethod
    def toDict(cls, task: TaskConfig):
        return {
            'name': task.name,
            'steps': list(map(lambda step: {
                'name': step.name,
                'implementation': step.implementation,
                'args': step.args}, task.steps))
        }

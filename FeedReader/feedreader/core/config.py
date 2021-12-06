from dataclasses import dataclass, field
from typing import List


class Class:

    def __init__(self, implementation: str, args: dict = None):
        self.implementation = implementation
        self.args = args if args else {}


class Step(Class):

    def __init__(self, name: str, implementation: str, args: dict = None):
        super().__init__(implementation, args)
        self.name = name


@dataclass
class Task:
    name: str
    steps: List[Step]

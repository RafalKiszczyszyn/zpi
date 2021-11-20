from dataclasses import dataclass
from typing import Callable, Type

from wordnet.core import events, controllers


@dataclass(frozen=True)
class Binding:
    queue: events.IQueue
    controller_factory: Callable[[], controllers.IQueueController]


def bind(queue: events.IQueue, controller: Type[controllers.IQueueController]) -> Binding:
    return Binding(queue, lambda: controller())

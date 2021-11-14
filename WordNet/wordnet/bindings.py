from typing import Tuple, Callable, Type, List

from wordnet import controllers, events


def bind(queue: str, controller: Type[controllers.IQueueController]) -> Tuple[str, Callable[[str], events.Response]]:
    return queue, lambda message: controller().consume(message)


bindings: List[Tuple[str, Callable[[str], events.Response]]] = [
    bind('test', controllers.TestQueueController)
]

from typing import List

from wordnet.core import bindings
from wordnet.service import controllers, events

BINDINGS: List[bindings.Binding] = [
    bindings.bind(
        queue=events.RabbitMqQueue(name='test', exchange=''),
        controller=controllers.TestQueueController),
    bindings.bind(
        queue=events.RabbitMqQueue(name='feed', exchange='feed'),
        controller=controllers.FeedQueueController
    )
]

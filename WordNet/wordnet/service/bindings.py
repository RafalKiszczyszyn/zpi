from dataclasses import dataclass
from typing import List

from zpi_common.services import events

from wordnet.service import handlers


@dataclass(frozen=True)
class Binding:
    topic: str
    handler: events.IEventHandler


def bindings() -> List[Binding]:
    return [
        Binding(topic='feed', handler=handlers.FeedEventHandler()),
        Binding(topic='scraps', handler=handlers.ScrapsEventHandler()),
        Binding(topic='', handler=handlers.ScrapsEventHandler())
    ]

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(eq=True, frozen=True)
class Enclosure:
    link: str
    length: int
    type: str


@dataclass(eq=True, frozen=True)
class Article:
    guid: str
    title: str
    summary: str
    published: datetime
    updated: datetime
    link: str
    enclosures: List[Enclosure]


@dataclass(eq=True, frozen=True)
class Channel:
    title: str
    updated: datetime
    lang: str
    contentNodes: List[str]
    articles: List[Article] = field(default_factory=lambda: [], hash=False)

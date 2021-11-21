from abc import ABC
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sample(ABC):
    index: int
    text: str
    pos: str


@dataclass(frozen=True)
class Word(Sample):
    pass


@dataclass(frozen=True)
class Phrase(Sample):
    words: int


@dataclass(frozen=True)
class SentimentAnnotation:
    sample: Sample
    annotation: int

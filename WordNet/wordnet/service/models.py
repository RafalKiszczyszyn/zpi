from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    summary: str


@dataclass(frozen=True)
class Segment:
    id: str
    segment: str
    sentiment: int

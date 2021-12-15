from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ScrappedArticle:
    id: str
    content: str


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    summary: str


class SegmentType(Enum):
    TITLE = 'title'
    SUMMARY = 'summary'
    CONTENT = 'content'


@dataclass(frozen=True)
class AnnotatedSegment:
    id: str
    segment: SegmentType
    polarity: float

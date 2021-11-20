from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    lemma: str
    pos: str


@dataclass(frozen=True)
class SentimentAnnotation:
    word: Word
    annotation: int

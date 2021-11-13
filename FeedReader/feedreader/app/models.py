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
    source: str
    title: str
    updated: datetime
    lang: str
    articles: List[Article] = field(default_factory=lambda: [], hash=False)


def default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return str(obj)


if __name__ == '__main__':
    channel = Channel(
        source='Polsat',
        title='Wiadomości z kraju',
        updated=datetime.utcnow(),
        lang='pl',
        articles=[
            Article(
                guid='abc',
                title='Nastał pokój',
                summary='Nastał pokój na świecie',
                published=datetime.utcnow(),
                updated=datetime.utcnow(),
                link='polsat/xd',
                enclosures=[
                    Enclosure(
                        link='dasdas',
                        length=600,
                        type='xd'
                    )
                ])
        ])
    raw = json.dumps(dataclasses.asdict(channel), ensure_ascii=False, default=default)
    print(raw)

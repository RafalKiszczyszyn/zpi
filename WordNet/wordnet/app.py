import asyncio

from wordnet import events, nlp
from wordnet import bindings


def main():
    nlp.get_pipeline()
    consumer = events.RabbitMqConsumer(
        loop=asyncio.get_event_loop(),
        bindings=bindings.bindings,
        threads=1,
        messages_limit=1)
    try:
        print('Started consuming...')
        consumer.consume()
    except KeyboardInterrupt:
        consumer.stop()


if __name__ == '__main__':
    main()

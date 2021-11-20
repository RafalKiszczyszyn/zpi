from dependency_injector.wiring import Provide, inject

from wordnet.service import containers
from wordnet.core import events, loggers


@inject
def startup(
        consumer: events.IQueueConsumer = Provide[containers.Container.IQueueConsumer],
        logger: loggers.ILogger = Provide[containers.Container.ILogger]):
    logger.info('Service started')
    try:
        start(consumer, logger)
    except KeyboardInterrupt:
        pass
    logger.info('Service stopped')


def start(
        consumer: events.IQueueConsumer,
        logger: loggers.ILogger):
    try:
        consumer.consume()
    except Exception as e:
        logger.error('During starting an event queue consumer, exception occurred', e)

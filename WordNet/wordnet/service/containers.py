from dependency_injector import containers, providers
from wordnet import settings
from wordnet.service import loggers, events, bindings as _bindings_
from wordnet.nlp.containers import NlpContainer


class Container(containers.DeclarativeContainer):

    ILogger = providers.Factory(
        loggers.StdoutLogger
    )

    bindings = providers.Object(
        _bindings_.BINDINGS
    )

    IQueueConsumer = providers.Factory(
        events.RabbitMqConsumer,
        bindings=bindings,
        logger=ILogger,
        exchange=settings.EXCHANGE,
        threads=settings.THREADS,
        messages_limit=settings.MESSAGES_LIMIT
    )

    nlp = providers.Container(
        NlpContainer
    )


def wire():
    container = Container()
    container.wire(packages=['wordnet.service'])

from dependency_injector import containers, providers
from . import config, persistence, sentiments


class NlpContainer(containers.DeclarativeContainer):

    connection_string = providers.Dependency()

    # Persistence
    ISentimentAnnotationsDataAccessFactory = providers.Factory(
        persistence.PlWordNetDataAccessFactory,
        connection_string=config.CONNECTION_STRING
    )
    ISentimentAnnotationsRepository = providers.Factory(
        persistence.SentimentAnnotationsRepository,
        data_access_factory=ISentimentAnnotationsDataAccessFactory
    )

    # Sentiments
    INlpPipeline = providers.Singleton(
        sentiments.SpacyPipeline,
        repository=ISentimentAnnotationsRepository
    )


def wire():
    NlpContainer().wire(packages=[__package__])

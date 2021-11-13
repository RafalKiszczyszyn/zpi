import ssl
from dataclasses import dataclass
from dependency_injector import containers, providers

import feedreader
from feedreader import settings
from feedreader.app import loggers, events, notifications, guid, persistance, logic
from feedreader.core import tasks


@dataclass
class AppSettings:
    heartbeat: int


Container = containers.DynamicContainer()


def create_container():
    container = containers.DynamicContainer()

    container.config = providers.Configuration(strict=True)

    container.settings = providers.Factory(
        AppSettings,
        heartbeat=container.config.heartbeat.as_int()
    )

    container.logger = providers.Factory(
        loggers.StdoutLogger
    )

    add_guid_generator(container, config_key='guid_generator')
    add_database_connection(container, config_key='database')
    add_event_publisher(container, config_key='event_queue')
    add_email_notifications(container, config_key='email_notifications')

    container.executor_provider = providers.Callable(
        tasks.task_executor_provider_factory
    )

    container.feed_reader_logic = providers.Factory(
        logic.FeedReaderLogic,
        articles_repository=container.articles_repository,
        event_publisher=container.event_publisher,
        logger=container.logger,
        email_service=container.email_service
    )

    return container


def add_guid_generator(container: containers.DynamicContainer, config_key):
    prefix = None
    postfix = None
    if config_key in settings.CONFIG:
        if 'prefix' in settings.CONFIG[config_key]:
            prefix = settings.CONFIG[config_key]['prefix']
        if 'postfix' in settings.CONFIG[config_key]:
            postfix = settings.CONFIG[config_key]['postfix']

    container.guid_generator = providers.Factory(
        guid.GuidGenerator,
        prefix=prefix,
        postfix=postfix
    )


def add_database_connection(container: containers.DynamicContainer, config_key):
    container.articles_da = providers.Factory(
        persistance.ArticlesDataAccess,
        url=settings.CONFIG[config_key]['connection_string'],
        db_name=settings.CONFIG[config_key]['database'],
        collection_name=settings.CONFIG[config_key]['collection'],
        ttl=settings.CONFIG[config_key]['ttl']
    )

    container.articles_repository = providers.Factory(
        persistance.ArticlesRepository,
        data_access=container.articles_da
    )


def add_event_publisher(container: containers.DynamicContainer, config_key):
    ssl_context = None

    if 'ssl' in settings.CONFIG[config_key]:
        ssl_context = {
            'cafile': str(settings.CONFIG[config_key]['ssl']["cafile"]),
            'certfile': str(settings.CONFIG[config_key]['ssl']["certfile"]),
            'keyfile': str(settings.CONFIG[config_key]['ssl']["keyfile"])
        }

    container.event_publisher = providers.Singleton(
        events.RabbitMQPublisher,
        url=container.config.event_queue.url,
        ssl_context=ssl_context
    )


def add_email_notifications(container: containers.DynamicContainer, config_key):
    if config_key not in settings.CONFIG:
        container.email_service = providers.Object(None)
        return

    container.smtp_connection = providers.Factory(
        notifications.TlsSecuredSmtpConnection,
        host=settings.CONFIG[config_key]['host'],
        port=settings.CONFIG[config_key]['port']
    )

    container.email_service = providers.Factory(
        notifications.EmailService,
        connection=container.smtp_connection,
        credentials=settings.CONFIG[config_key]['credentials'],
        template=str(settings.CONFIG[config_key]['template']),
        recipients=settings.CONFIG[config_key]['recipients'],
        logger=container.logger
    )


def wire():
    global Container
    container = create_container()
    container.config.from_dict(settings.CONFIG, required=True)

    Container = container
    container.wire(packages=[feedreader])

import ssl
from dataclasses import dataclass
from typing import Union

from dependency_injector import containers, providers
from zpi_common.services import loggers, notifications
from zpi_common.services.implementations import rabbitmq

import feedreader
from feedreader import settings
from feedreader.service import persistance, logic
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

    add_database_connection(container, config_key='database')
    add_event_queue_connection(container, config_key='event_queue')
    add_email_notifications(container, config_key='email_notifications')

    container.executor_provider = providers.Callable(
        tasks.task_executor_provider_factory
    )

    container.feed_reader_logic = providers.Factory(
        logic.FeedReaderLogic,
        articles_repository=container.articles_repository,
        event_queue_connection_factory=container.event_queue_connection_factory,
        logger=container.logger,
        email_service=container.email_service
    )

    return container


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


def add_event_queue_connection(container: containers.DynamicContainer, config_key):
    context: Union[ssl.SSLContext(), None] = None
    if 'ssl' in settings.CONFIG[config_key]:
        try:
            context = ssl.SSLContext()
            context.load_verify_locations(str(settings.CONFIG[config_key]['ssl']["cafile"]))
            context.load_cert_chain(
                str(settings.CONFIG[config_key]['ssl']["certfile"]),
                str(settings.CONFIG[config_key]['ssl']["keyfile"]))
        except FileNotFoundError as e:
            print(f'Skipping SSL configuration because: {e}')

    class ConfigProvider(rabbitmq.IConfigProvider):

        def queue(self) -> rabbitmq.QueueConfig:
            return rabbitmq.QueueConfig(
                name=f'feedreader.queue', durable=True, auto_delete=False, exclusive=False)

        def fanout(self, topic: str) -> rabbitmq.FanoutConfig:
            return rabbitmq.FanoutConfig(name=topic, durable=True, auto_delete=False)

    container.event_queue_connection_factory = providers.Factory(
        rabbitmq.RabbitMqConnectionFactory,
        params=rabbitmq.RabbitMqConnectionParams(
            host=settings.CONFIG[config_key]["host"],
            vhost=settings.CONFIG[config_key]["vhost"],
            username=settings.CONFIG[config_key]["username"],
            password=settings.CONFIG[config_key]["password"],
            sslContext=context,
            configProvider=ConfigProvider()
        )
    )


def add_email_notifications(container: containers.DynamicContainer, config_key):
    if config_key not in settings.CONFIG:
        container.email_service = providers.Object(None)
        return

    container.email_service = providers.Factory(
        notifications.EmailBroadcastService,
        connection=container.smtp_connection,
        credentials=(settings.CONFIG[config_key]['credentials']['username'],
                     settings.CONFIG[config_key]['credentials']['password']),
        recipients=settings.CONFIG[config_key]['recipients'],
        connection_factory=notifications.TlsSecuredSmtpConnectionFactory(
            host=settings.CONFIG[config_key]['host'], port=settings.CONFIG[config_key]['port']),
        logger=container.logger
    )


def wire():
    global Container
    container = create_container()
    container.config.from_dict(settings.CONFIG, required=True)

    Container = container
    container.wire(packages=[feedreader])

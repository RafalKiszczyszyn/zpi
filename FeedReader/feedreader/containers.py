from dataclasses import dataclass
from dependency_injector import containers, providers

import feedreader
from feedreader import settings, loggers, notifications, workers, events


@dataclass
class AppSettings:
    heartbeat: int


class Container(containers.DeclarativeContainer):

    config = providers.Configuration(strict=True)

    settings = providers.Factory(
        AppSettings,
        heartbeat=config.heartbeat.as_int()
    )

    logger = providers.Singleton(
        loggers.FileLogger,
        filename=config.logger.filename
    )

    smtp_connection = providers.Singleton(
        notifications.TlsSecuredSmtpConnection,
        host=config.email_notifications.host,
        port=config.email_notifications.port,
    )

    email_service = providers.Singleton(
        notifications.EmailService,
        connection=smtp_connection,
        credentials=config.email_notifications.credentials,
        template=config.email_notifications.template,
        recipients=config.email_notifications.recipients,
        logger=logger
    )

    event_publisher = providers.Singleton(
        events.RabbitMQPublisher,
        url=config.event_queue.url,
        exchange=config.event_queue.channel
    )

    __email_service_worker = providers.Singleton(
        workers.EmailServiceBackgroundWorker,
        name='Email Service',
        logger=logger,
        email_service=email_service
    )

    __event_queue_worker = providers.Singleton(
        workers.EventQueueBackgroundWorker,
        name='Event Queue',
        logger=logger,
        publisher=event_publisher
    )

    dispatcher = providers.Singleton(
        workers.BackgroundJobDispatcher,
        email_service_worker=__email_service_worker,
        event_queue_worker=__event_queue_worker
    )


CONTAINER: Container


def wire():
    global CONTAINER

    CONTAINER = Container()
    CONTAINER.config.from_dict(settings.CONFIG, required=True)
    CONTAINER.wire(packages=[feedreader])

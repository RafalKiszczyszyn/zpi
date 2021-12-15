import ssl
from typing import Union

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from zpi_common.services import loggers, notifications
from zpi_common.services.implementations import rabbitmq

from wordnet import settings
from wordnet.nlp import nlp, persistence
from wordnet.service.events import EventLoop


def connection() -> rabbitmq.RabbitMqConnectionFactory:
    context: Union[ssl.SSLContext(), None] = None
    if hasattr(settings, 'SSL_ENABLED') and settings.SSL_ENABLED:
        context = ssl.SSLContext()
        context.load_verify_locations(str(settings.SSL_CA))
        context.load_cert_chain(str(settings.SSL_CERT), str(settings.SSL_KEY))

    class ConfigProvider(rabbitmq.IConfigProvider):

        def queue(self) -> rabbitmq.QueueConfig:
            return rabbitmq.QueueConfig(
                name=f'{settings.QUEUE_NAME_PREFIX}.queue', durable=True, auto_delete=False, exclusive=False)

        def fanout(self, topic: str) -> rabbitmq.FanoutConfig:
            return rabbitmq.FanoutConfig(name=topic, durable=False, auto_delete=True)

    return rabbitmq.RabbitMqConnectionFactory(rabbitmq.RabbitMqConnectionParams(
        host=settings.HOST,
        vhost=settings.VHOST,
        username=settings.USERNAME,
        password=settings.PASSWORD,
        sslContext=context,
        configProvider=ConfigProvider()
    ))


def addServices(container: containers.DynamicContainer):
    container.ILogger = providers.Factory(
        loggers.StdoutLogger
    )

    container.IConnectionFactory = providers.Callable(connection)

    if hasattr(settings, 'NOTIFICATIONS_ENABLED') and settings.NOTIFICATIONS_ENABLED:
        container.IEmailBroadcastService = providers.Factory(
            notifications.EmailBroadcastService,
            credentials=(settings.NOTIFICATIONS_USERNAME, settings.NOTIFICATIONS_PASSWORD),
            recipients=settings.NOTIFICATIONS_RECIPIENTS,
            connection_factory=notifications.TlsSecuredSmtpConnectionFactory(
                host=settings.NOTIFICATIONS_HOST, port=settings.NOTIFICATIONS_PORT),
            logger=container.ILogger
        )
    else:
        container.IEmailBroadcastService = providers.Object(None)

    container.INlpService = providers.Factory(
        nlp.ClarinNlpService,
        user=settings.CLARIN_USER,
        algorithm=nlp.Average(),
        manager=persistence.WorkspaceManager(wd=str(settings.CLARIN_WORKING_DIRECTORY))
    )


def startup():
    container = containers.DynamicContainer()
    addServices(container)
    container.wire(packages=['wordnet.service'])
    start()


@inject
def start(logger: loggers.ILogger = Provide[loggers.ILogger.__name__],
          emailService: Union[notifications.IEmailBroadcastService, None]
          = Provide[notifications.IEmailBroadcastService.__name__]):
    logger.info('Service started')
    try:
        EventLoop().start()
    except KeyboardInterrupt:
        EventLoop().stop()
    except Exception as e:
        from traceback import TracebackException
        logger.error('Fatal exception was thrown', error=e)
        notify(emailService=emailService, logger=logger, error=e)
    logger.info('Service stopped')


def notify(
        emailService: notifications.IEmailBroadcastService,
        logger: loggers.ILogger,
        error: Exception):
    from traceback import TracebackException
    if emailService:
        try:
            logger.info('Sending email notification')
            emailService.info(
                title='WordNet Service Fatal Failure',
                message='Unrecoverable fatal exception was thrown. Service stopped!',
                traceback="".join(TracebackException.from_exception(error).format()))
        except Exception as e:
            logger.error("Failed to send email notification", error=e)

import smtplib
from typing import List, Tuple

from zpi_common.services.loggers import StdoutLogger
from zpi_common.services.notifications import ISmtpConnection, ISmtpConnectionFactory, EmailBroadcastService
from zpi_common.services.events import IQueueController, Response, Ack, IQueueControllerFactory, RabbitMqConnection, \
    RabbitMqQueue, EventQueueClient, Binding

DEBUGGING_SERVER_CMD = 'python -m smtpd -n -c DebuggingServer localhost:1000'


class DebuggingSmtpConnection(ISmtpConnection):

    def __init__(self, host: str, port: int):
        server = smtplib.SMTP(host, port)
        self._server = server

    def __enter__(self) -> ISmtpConnection:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.close()

    def send_email(self, sender: str, recipients: List[str], message: str):
        self._server.sendmail(sender, recipients, message)


class DebuggingSmtpConnectionFactory(ISmtpConnectionFactory):

    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port

    def create(self, credentials: Tuple[str, str]) -> ISmtpConnection:
        return DebuggingSmtpConnection(self._host, self._port)


class DebuggingController(IQueueController):

    def consume(self, queue: str, message: str) -> Response:
        print(f"Queue='{queue}', Message='{message}'")
        return Ack()


class DebuggingControllerFactory(IQueueControllerFactory):

    def create(self) -> IQueueController:
        return DebuggingController()


def send_email():
    service = EmailBroadcastService(
        credentials=('', ''),
        recipients=[''],
        templates={EmailBroadcastService.ERROR_TEMPLATE_NAME: 'template.str'},
        connection_factory=DebuggingSmtpConnectionFactory(host='localhost', port=1000),
        logger=StdoutLogger())
    service.error('Info', body='This is a message body.')


def consume():
    queues = ['test']
    bindings = [Binding('test', DebuggingControllerFactory())]

    connection = RabbitMqConnection(
        fanout='test',
        queues=[RabbitMqQueue(name=queue) for queue in queues],
        logger=StdoutLogger()
    )

    client = EventQueueClient(connection=connection, logger=StdoutLogger())
    client.consume(bindings)


if __name__ == '__main__':
    consume()

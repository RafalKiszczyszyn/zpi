import asyncio
import signal
from typing import Union

from dependency_injector.wiring import inject, Provide
from zpi_common.services import events, loggers

from wordnet import settings
from wordnet.service import bindings


class EventLoop:

    def handleTerminationSignal(self):
        self._dispose()
        self._loop.stop()

    class RecoverableError(Exception):
        def __init__(self, error: Exception):
            self._error = error

        @property
        def error(self):
            return self._error

    class EventReturned(Exception):
        pass

    class UnknownResult(Exception):
        def __init__(self, topic):
            super().__init__(f"Topic='{topic}': Handler returned unknown result")

    class MissingBinding(Exception):
        def __init__(self, topic):
            super().__init__(f"Topic='{topic}': Missing binding")

    @inject
    def __init__(self, connection_factory: events.IConnectionFactory = Provide[events.IConnectionFactory.__name__],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        signal.signal(signal.SIGTERM, self.handleTerminationSignal)

        self._connection_factory = connection_factory
        self._logger = logger

        self._loop = asyncio.get_event_loop()
        self._connection: Union[events.IConnection, None] = None
        self._publisher: Union[events.IChannel, None] = None
        self._consumer: Union[events.IChannel, None] = None
        self._bindings = bindings.bindings()

    def start(self):
        self._loop.run_until_complete(self._run())

    def stop(self):
        if self._consumer:
            self._consumer.cancel()
        self._loop.call_soon_threadsafe(self._cancel)

    def _cancel(self):
        self._dispose()
        self._loop.stop()

    def _dispose(self):
        self._logger.info('Closing connection with an event queue')
        if self._connection and not self._connection.is_closed:
            self._connection.close()

    async def _run(self):
        stopped = False
        while not stopped:
            try:
                await self._consume()
            except self.RecoverableError as e:
                self._logger.error('Exception caught when consuming events', error=e)
            except self.EventReturned:
                self._logger.warning('Event was requeued')
            finally:
                self._dispose()
            self._logger.info(f'Retrying in {settings.RESTART} seconds')
            await asyncio.sleep(settings.RESTART)

    async def _consume(self):
        await self._connect()
        self._logger.info('Started consuming events')
        for event in self._consumer.consume():
            await self._handle_event(event)

    async def _connect(self):
        self._logger.info('Connected with an event queue')
        try:
            self._connection = self._connection_factory.create()
            self._publisher = self._connection.publisher(topic='sentiments')
            self._consumer = self._connection.consumer(topics=list({binding.topic for binding in self._bindings}))
        except Exception as e:
            raise self.RecoverableError(error=e)

    async def _handle_event(self, event: events.Event):
        self._logger.info(f'Received {event}')
        result = await self._dispatch(event)

        if isinstance(result, events.Accept):
            await self._accept(result)
        elif isinstance(result, events.Reject):
            await self._reject(result)
        else:
            raise EventLoop.UnknownResult(topic=event.topic)

    async def _dispatch(self, event: events.Event) -> events.Result:
        for binding in self._bindings:
            if binding.topic == event.topic:
                return binding.handler.handle(event)
        raise self.MissingBinding(topic=event.topic)

    async def _accept(self, result: events.Accept):
        if result.message:
            try:
                message = events.Message(body=result.message, mandatory=True, persistence=False)
                self._logger.info(f'Publishing {message}')
                self._publisher.publish(events.Message(body=result.message, mandatory=True, persistence=False))
            except Exception as e:
                raise self.RecoverableError(error=e)
            finally:
                self._publisher.reject(result.event, requeue=True)

        self._logger.info(f'Accepting {result.event}')
        self._consumer.accept(event=result.event)

    async def _reject(self, result: events.Reject):
        self._logger.info(f'Rejecting {result.event}')
        if result.requeue:
            self._consumer.reject(event=result.event, requeue=True)
            raise EventLoop.EventReturned()
        else:
            self._consumer.reject(event=result.event, requeue=False)

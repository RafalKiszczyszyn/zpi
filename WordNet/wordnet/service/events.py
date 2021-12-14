import asyncio
import signal
from traceback import TracebackException
from typing import Union, List

from dependency_injector.wiring import inject, Provide
from zpi_common.services import events, loggers, notifications

from wordnet import settings
from wordnet.service import bindings as bdgs, functional


class InternalException(Exception):
    pass


class FatalException(Exception):
    pass


class EventLoop:

    def handleTerminationSignal(self):
        self._dispose()
        self._loop.stop()

    @inject
    def __init__(self,
                 connection_factory: events.IConnectionFactory = Provide[events.IConnectionFactory.__name__],
                 logger: loggers.ILogger = Provide[loggers.ILogger.__name__]):
        signal.signal(signal.SIGTERM, self.handleTerminationSignal)

        self._connection_factory = connection_factory
        self._logger = logger

        self._loop = asyncio.get_event_loop()
        self._connection: Union[events.IConnection, None] = None
        self._publisher: Union[events.IChannel, None] = None
        self._consumer: Union[events.IChannel, None] = None

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
            except InternalException:
                pass
            finally:
                self._dispose()
            await self._sleep(settings.RESTART)

    async def _sleep(self, seconds: int):
        self._logger.info(f'Event Loop state changed into sleep state. Wake up in {seconds} seconds')
        await asyncio.sleep(seconds)

    async def _consume(self):
        await self._connect()
        self._logger.info('Starting consuming events')
        for event in self._consumer.consume():
            self._logger.info(f'Received {event}')
            dispatcher = EventDispatcher(
                bindings=bdgs.bindings(),
                consumer=self._consumer,
                publisher=self._publisher)
            result = dispatcher.dispatch(event)
            await self._handleDispatchingResult(event, result)

    async def _connect(self):
        self._logger.info('Attempting connection with an event queue')
        try:
            self._connection = self._connection_factory.create()
            self._publisher = self._connection.publisher(topic=settings.FANOUT)
            self._consumer = self._connection.consumer(topics=list({binding.topic for binding in bdgs.bindings()}))
        except Exception as e:
            self._logger.error("Connection with an event queue failed", error=e)
            await self._notify("WordNet Service Failure when connecting", error=e)
            raise InternalException()
        self._logger.info('Successfully connected with an event queue')

    async def _handleDispatchingResult(self, event: events.Event, result: functional.Result):
        if result.isSuccess:
            if result.value:
                self._logger.info(f'Successfully published response to {event}')
            else:
                self._logger.warning(f'Response was not sent to {event}')
            return

        if result.error.isRuntime:
            self._logger.error("Internal exception raised when consuming events", error=result.error.exception)
            await self._notify("WordNet Service Failure when consuming", error=result.error.exception)
            raise InternalException()
        else:
            raise FatalException(result.error.message)

    @inject
    async def _notify(
            self,
            title: str,
            error: Union[Exception, None] = None,
            service: notifications.IEmailBroadcastService = Provide[notifications.IEmailBroadcastService.__name__],
            **tags):
        if issubclass(type(service), notifications.IEmailBroadcastService):
            self._logger.info('Sending email notification')
            try:
                service.error(
                    title=title,
                    traceback="".join(TracebackException.from_exception(error).format()) if error else "Not provided",
                    **tags)
            except Exception as e:
                self._logger.error("Failed to send email notification", error=e)


class EventDispatcher:

    def __init__(self,
                 bindings: List[bdgs.Binding],
                 consumer: events.IChannel,
                 publisher: events.IChannel):
        self.bindings = bindings
        self.consumer = consumer
        self.publisher = publisher

    def dispatch(self, event: events.Event) -> functional.Result:
        return self.matchBinding(event) \
            .then(self.handleEvent) \
            .then(self.handleResponse)

    def matchBinding(self, event: events.Event) -> functional.Result:
        for binding in self.bindings:
            if binding.topic == event.topic:
                return functional.Result.success((event, binding))
        return self.rejectEvent(response=events.Reject(event, requeue=True), cause=functional.Error(
            message=f"Missing binding with topic={event.topic}",
            isRuntime=False))

    def handleEvent(self, event: events.Event, binding: bdgs.Binding) -> functional.Result:
        try:
            return functional.Result.success(binding.handler.handle(event))
        except Exception as e:
            return self.rejectEvent(response=events.Reject(event, requeue=True), cause=functional.Error(
                message="Failed to handle an event",
                isRuntime=True,
                exception=e))

    def handleResponse(self, response: events.Result) -> functional.Result:
        if isinstance(response, events.Accept):
            return self.acceptEvent(response)
        elif isinstance(response, events.Reject):
            return self.rejectEvent(response)
        return functional.Result.failure(functional.Error(
            message="Unknown response returned by handler",
            isRuntime=False))

    def acceptEvent(self, response: events.Accept) -> functional.Result:
        return self.publishResponse(response) \
            .then(lambda isPublished: self.sendAcceptAck(response, isPublished))

    def publishResponse(self, response: events.Accept) -> functional.Result:
        if response.message:
            message = events.Message(body=response.message, mandatory=True, persistence=False)
            try:
                self.publisher.publish(message)
                return functional.Result.success(True)
            except Exception as e:
                return self.rejectEvent(
                    events.Reject(event=response.event, requeue=True),
                    cause=functional.Error(
                        message=f"Failed to publish {message} as a response to {response.event}",
                        isRuntime=True,
                        exception=e))

        return functional.Result.success(False)

    def sendAcceptAck(self, response: events.Accept, isPublished: bool) -> functional.Result:
        self.consumer.accept(event=response.event)
        return functional.Result.success(isPublished)

    def rejectEvent(self, response: events.Reject, cause: Union[functional.Error, None] = None) -> functional.Result:
        self.consumer.reject(event=response.event, requeue=response.requeue)
        return functional.Result.success(False) \
            if not response.requeue \
            else functional.Result.failure(cause if cause else functional.Error(
                message=f"{response.event} requeued", isRuntime=True))

import asyncio
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dependency_injector.wiring import inject

from feedreader import loggers, notifications, events


@dataclass
class BackgroundJob:
    name: str


@dataclass
class EmailBackgroundJob(BackgroundJob):
    title: str
    content: str


@dataclass
class EventQueueBackgroundJob(BackgroundJob):
    channel: str
    content: str


class AbstractBackgroundWorker(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def ensure_started(self):
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass

    @abstractmethod
    def enqueue_job(self, job: BackgroundJob) -> bool:
        pass

    @abstractmethod
    def jobs_count(self) -> int:
        pass

    @abstractmethod
    def stop(self, force=False) -> bool:
        pass


class AsyncioBackgroundWorkerBase(AbstractBackgroundWorker):

    @inject
    def __init__(self, name, rate=1):
        self._stopped = True
        self._thread = threading.Thread(target=self._run)
        self._thread.name = name
        self._loop = asyncio.get_event_loop()
        self._queue = queue.Queue()
        self._rate = rate

    def start(self):
        self._stopped = False
        self._thread.start()

    def ensure_started(self):
        if not self.is_running():
            self.start()
            while not self.is_running():
                pass

    def is_running(self):
        return self._thread.is_alive()

    def enqueue_job(self, job: BackgroundJob) -> bool:
        if self._stopped:
            return False

        self._on_job_enqueue(job)
        self._queue.put_nowait(job)
        return True

    def jobs_count(self):
        return self._queue.qsize()

    def stop(self, force=False) -> bool:
        if self._stopped:
            return True

        if force or self._queue.empty():
            self._on_stop()
            self._stopped = True
            return True

        return False

    def _run(self):
        self._on_start()
        self._loop.run_until_complete(self._consume())

    async def _consume(self):
        while not self._stopped:
            if not self._queue.empty():
                try:
                    job = self._queue.get_nowait()
                    self._on_job_consume(job)
                except queue.Empty:
                    pass
            await asyncio.sleep(1 / self._rate)

    @abstractmethod
    def _on_start(self):
        pass

    @abstractmethod
    def _on_job_enqueue(self, job: BackgroundJob):
        pass

    @abstractmethod
    def _on_job_consume(self, job: BackgroundJob):
        pass

    @abstractmethod
    def _on_stop(self):
        pass


class EmailServiceBackgroundWorker(AsyncioBackgroundWorkerBase):

    def __init__(self, name, logger: loggers.LoggerBase, email_service: notifications.EmailServiceBase):
        super().__init__(name)
        self._logger = logger
        self._email_service = email_service

    def _on_start(self):
        self._log("Started.")

    def _on_job_enqueue(self, job: BackgroundJob):
        if type(job) is not EmailBackgroundJob:
            raise TypeError(f'Job must be type of {EmailBackgroundJob.__name__}')
        self._log(f"Enqueued job='{job.name}'.")

    def _on_job_consume(self, job: EmailBackgroundJob):
        try:
            self._log(f"Sending email with title='{job.title}'.")
            self._email_service.broadcast(job.title, job.content)
        except notifications.EmailServiceException as e:
            self._log(f"Sending email with title='{job.title}' failed with error: {e}.")

    def _on_stop(self):
        self._log("Stopped.")

    def _log(self, content):
        self._logger.log(f"(BackgroundWorker='{self._thread.name}') {content}")


class EventQueueBackgroundWorker(AsyncioBackgroundWorkerBase):

    def __init__(self, name, logger: loggers.LoggerBase, publisher: events.AbstractEventQueuePublisher):
        super().__init__(name)
        self._logger = logger
        self._publisher = publisher

    def _on_start(self):
        self._log("Started.")

    def _on_job_enqueue(self, job: BackgroundJob):
        if type(job) is not EventQueueBackgroundJob:
            raise TypeError(f'Job must be type of {EventQueueBackgroundJob.__name__}')
        self._log(f"Enqueued job='{job.name}'.")

    def _on_job_consume(self, job: EventQueueBackgroundJob):
        try:
            self._log(f"Publishing event.")
            self._publisher.connect()
            self._publisher.publish(job.content)
            self._publisher.close()
        except Exception as e:
            self._log(f"Publishing event failed with error: {e}.")

    def _on_stop(self):
        self._log("Stopped.")

    def _log(self, content):
        self._logger.log(f"(BackgroundWorker='{self._thread.name}') {content}")


class BackgroundJobDispatcher:

    def __init__(self,
                 email_service_worker: AbstractBackgroundWorker,
                 event_queue_worker: AbstractBackgroundWorker):
        self._workers = {
            EmailBackgroundJob: email_service_worker,
            EventQueueBackgroundJob: event_queue_worker
        }

    def enqueue_job(self, job: BackgroundJob):
        job_type = type(job)
        if job_type not in self._workers:
            raise Exception(f'Unsupported {BackgroundJob.__name__} type: {job_type}')

        worker = self._workers[job_type]
        worker.ensure_started()
        worker.enqueue_job(job)

    def dispose(self):
        for job_type in self._workers:
            self._workers[job_type].stop(force=True)


if __name__ == '__main__':
    dispatcher = BackgroundJobDispatcher(
        email_service_worker=EmailServiceBackgroundWorker(
            name='Email Service',
            logger=loggers.DebugLogger(),
            email_service=notifications.EmailService(
                credentials={'username': 'username'},
                recipients=['example@example'],
                template='template.html',
                connection=notifications.SmtpDebugConnection(port=1000),
                logger=loggers.DebugLogger())),
        event_queue_worker=EventQueueBackgroundWorker(
            name='Event Queue',
            logger=loggers.DebugLogger(),
            publisher=events.RabbitMQPublisher(
                url='amqp://guest:guest@localhost:5672/%2f?heartbeat=60',
                exchange='feed')
        ))

    dispatcher.enqueue_job(EventQueueBackgroundJob(name='XDD', channel='XD', content='Come on!'))
    time.sleep(15)
    dispatcher.dispose()

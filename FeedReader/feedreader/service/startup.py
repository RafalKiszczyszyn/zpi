import asyncio
import signal
from contextlib import contextmanager

from dependency_injector.wiring import Provide, inject
from zpi_common.services import loggers

from feedreader import containers, settings
from feedreader.core import tasks


async def execute_tasks(executor: tasks.ITaskExecutor):
    executor.execute()


def handleTerminationSignal(logger: loggers.ILogger, loop: asyncio.AbstractEventLoop):
    logger.info('FeedReader stopped.')
    loop.stop()


@inject
async def run(
        executor_provider: tasks.ITaskExecutorProvider = Provide[containers.Container.executor_provider],
        app_settings: containers.AppSettings = Provide[containers.Container.settings],
        logger: loggers.ILogger = Provide[containers.Container.logger]):
    try:
        signal.signal(signal.SIGTERM, lambda: handleTerminationSignal(logger, asyncio.get_event_loop()))

        logger.info('FeedReader started.')
        logger.info('Loading tasks from settings.')
        executor = executor_provider.load_from_config(settings.EXECUTOR, settings.TASKS)
        logger.info(f'Loaded {executor.tasks_count} task(s).')

        running = True
        while running:
            task = asyncio.create_task(execute_tasks(executor))
            if app_settings.heartbeat > 0:
                await asyncio.sleep(app_settings.heartbeat)
            else:
                await task
                running = False

    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(message='During tasks execution an unexpected exception occurred:', error=e)
    finally:
        logger.info('FeedReader stopped.')
        asyncio.get_event_loop().stop()


def startup():
    asyncio.get_event_loop().run_until_complete(run())

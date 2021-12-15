import asyncio
import signal

from dependency_injector.wiring import Provide, inject
from zpi_common.services import loggers

from feedreader import containers
from feedreader.settings import settings
from feedreader.apirest import management
from feedreader.core import tasks


async def execute_tasks(executor: tasks.ITaskExecutor):
    executor.execute()


@inject
async def run(
        app_settings: containers.AppSettings = Provide[containers.Container.settings],
        management_service: management.ManagementService = Provide[containers.Container.management_service],
        executor_provider: tasks.ITaskExecutorProvider = Provide[containers.Container.executor_provider],
        logger: loggers.ILogger = Provide[containers.Container.logger]):
    try:
        if management_service is not None:
            logger.info('Starting management server')
            management_service.startServer()

        def handleTerminationSignal(loop: asyncio.AbstractEventLoop):
            if management_service is not None:
                logger.info('Stopping management server')
                management_service.stopServer()
            logger.info('FeedReader stopped.')
            loop.stop()
        signal.signal(signal.SIGTERM, lambda: handleTerminationSignal(asyncio.get_event_loop()))

        logger.info('FeedReader started.')
        running = True
        while running:
            logger.info('Loading tasks from settings.')
            executor = executor_provider.loadFromJsonFile(settings.EXECUTOR, settings.SOURCES)
            logger.info(f'Loaded {executor.tasks_count} task(s).')
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

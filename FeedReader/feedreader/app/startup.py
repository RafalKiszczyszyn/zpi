import asyncio
from dependency_injector.wiring import Provide, inject

from feedreader import containers, settings
from feedreader.core import tasks
from feedreader.app import loggers


async def execute_tasks(executor: tasks.ITaskExecutor):
    executor.execute()


@inject
async def run(
        executor_provider: tasks.ITaskExecutorProvider = Provide[containers.Container.executor_provider],
        app_settings: containers.AppSettings = Provide[containers.Container.settings],
        logger: loggers.LoggerBase = Provide[containers.Container.logger]):
    try:
        logger.log('FeedReader started.')
        logger.log('Loading tasks from settings.')
        executor = executor_provider.load_from_config(settings.EXECUTOR, settings.TASKS)
        logger.log(f'Loaded {executor.tasks_count} task(s).')

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
        logger.log_error(info='During tasks execution an unexpected exception occurred:', e=e)
    finally:
        logger.log('FeedReader stopped.')
        asyncio.get_event_loop().stop()


def startup():
    asyncio.get_event_loop().run_until_complete(run())

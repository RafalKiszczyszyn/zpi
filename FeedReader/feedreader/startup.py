import time

from dependency_injector.wiring import Provide, inject

from feedreader import core, tasks, containers, workers, settings


def load_tasks(config_tasks):
    implementation_builder = core.implementation_builder_factory()
    task_builder = tasks.TaskBuilder(implementation_builder)
    tasks_ = []
    for config_task in config_tasks:
        task = task_builder.build(config_task)
        tasks_.append(task)

    return tasks_


@inject
def startup(
        app_settings: containers.AppSettings = Provide[containers.Container.settings],
        dispatcher: workers.BackgroundJobDispatcher = Provide[containers.Container.dispatcher]):
    try:
        while True:
            tasks_ = load_tasks(settings.TASKS)

            for task in tasks_:
                task.execute()

            time.sleep(app_settings.heartbeat)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Unexpected exception: {e}')
    print('Stopping...')
    dispatcher.dispose()

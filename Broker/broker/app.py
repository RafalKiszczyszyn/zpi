from broker import core, config, builders
from broker.server import HttpServer


def load_services():
    implementation_builder = core.implementation_builder_factory({})
    service_builder = builders.ServiceBuilder(implementation_builder)

    return service_builder.build(config.SERVICES)


def load_tasks(services):
    meta_resolver = core.MetaResolver(services)
    implementation_builder = core.implementation_builder_factory(services)
    task_builder = builders.TaskBuilder(implementation_builder, meta_resolver)
    tasks = []
    for config_task in config.TASKS:
        task = task_builder.build(config_task)
        tasks.append(task)

    return tasks


def listen(host, port, *args, **kwargs):
    try:
        server = HttpServer(host, port, *args, **kwargs)
        server.serve_forever()
    except Exception as e:
        raise Exception(f"Could not start server with message: {e}")


def startup():
    services = load_services()
    tasks = load_tasks(services)
    listen(config.HOST, config.PORT, endpoint=config.EVENT_ENDPOINT, tasks=tasks)


if __name__ == '__main__':
    startup()

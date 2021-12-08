import dataclasses
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from traceback import TracebackException
from typing import Union, Tuple
from werkzeug.serving import make_server

from dependency_injector.wiring import Provide, inject
from flask import Flask, request
from flask_restful import Resource, Api

from feedreader import settings
from feedreader.core import config, tasks


@dataclass(frozen=True)
class Error:
    message: str
    traceback: Union[str, None] = None


class Tasks(Resource):

    @inject
    def __init__(self, taskBuilder: tasks.ITaskBuilder = Provide['task_builder']):
        self._taskBuilder = taskBuilder
        self._taskMapper = config.TaskConfigMapper()

    @classmethod
    def get(cls):
        with open(settings.SOURCES, 'r') as file:
            tasks_ = json.load(file)
        return tasks_, 200

    def post(self):
        task, error = self._validate()
        if error:
            return dataclasses.asdict(error), 400

        with open(settings.SOURCES, 'r+') as file:
            tasks_ = json.load(file)
            tasks_.append(self._taskMapper.toDict(task))

            file.seek(0)
            json.dump(tasks_, file, indent=4)

        return None, 201

    @classmethod
    def delete(cls, taskName: str = 'Undefined'):
        if taskName == 'Undefined':
            return None, 404

        with open(settings.SOURCES, 'r') as file:
            tasks_ = json.load(file)
        filtered = list(filter(lambda task: task['name'].lower() != taskName.lower(), tasks_))
        with open(settings.SOURCES, 'w') as file:
            json.dump(filtered, file, indent=4)

        deleted = len(tasks_) - len(filtered)
        if deleted == 0:
            return None, 404
        else:
            return deleted, 200

    def _validate(self) -> Tuple[Union[config.TaskConfig, None], Union[Error, None]]:
        task_ = request.get_json(force=True)
        try:
            task = self._taskMapper.fromDict(task_)
        except KeyError as e:
            return None, Error(message=str(e).strip('"'))
        except Exception as e:
            return None, Error(message=f'Invalid request. Exception: {e}')

        try:
            self._taskBuilder.build(task)
        except Exception as e:
            traceback = "".join(TracebackException.from_exception(e).format())
            return None, Error(message='Task has not built properly', traceback=traceback)

        return task, None


class IManagementService(ABC):

    @abstractmethod
    def startServer(self):
        pass

    @abstractmethod
    def stopServer(self):
        pass


class ManagementService(IManagementService):

    def __init__(self, host, port):
        app = Flask('Feed Reader Management')
        api = Api(app)
        api.add_resource(Tasks, '/tasks', '/tasks/<taskName>')
        self._server = make_server(host, port, app)

    def _run(self):
        self._server.serve_forever()

    def startServer(self):
        threading.Thread(target=self._run).start()

    def stopServer(self):
        self._server.shutdown()

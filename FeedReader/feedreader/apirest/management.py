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

from feedreader.core import config, tasks


@dataclass(frozen=True)
class Error:
    message: str
    traceback: Union[str, None] = None


class Request:

    @classmethod
    def getJson(cls):
        return request.get_json(force=True)


class Tasks(Resource):

    @inject
    def __init__(self,
                 appSettings=Provide['settings'],
                 taskBuilder: tasks.ITaskBuilder = Provide['task_builder']):
        self._appSettings = appSettings
        self._taskBuilder = taskBuilder
        self._taskMapper = config.TaskConfigMapper()

    def get(self):
        tasks_ = self._loadTasksFromConfig()
        return tasks_, 200

    def post(self):
        task, error = self._validate()
        if error:
            return dataclasses.asdict(error), 400

        tasks_ = self._loadTasksFromConfig()
        tasks_.append(self._taskMapper.toDict(task))
        self._saveTasksToConfig(tasks_)

        return None, 201

    def delete(self, taskName: str = 'Undefined'):
        if taskName == 'Undefined':
            return None, 404

        tasks_ = self._loadTasksFromConfig()
        filtered = list(filter(lambda task: task['name'].lower() != taskName.lower(), tasks_))
        self._saveTasksToConfig(filtered)

        deleted = len(tasks_) - len(filtered)
        if deleted == 0:
            return None, 404
        else:
            return deleted, 200

    def _loadTasksFromConfig(self):
        with open(self._appSettings.sources, 'r') as file:
            try:
                tasks_ = json.load(file)
                if not isinstance(tasks_, list):
                    return []
            except json.JSONDecodeError:
                return []
        return tasks_

    def _saveTasksToConfig(self, tasks_):
        with open(self._appSettings.sources, 'w') as file:
            json.dump(tasks_, file, indent=4)

    def _validate(self) -> Tuple[Union[config.TaskConfig, None], Union[Error, None]]:
        task_ = Request().getJson()

        try:
            task = self._taskMapper.fromDict(task_)
        except KeyError as e:
            return None, Error(message=str(e).strip('"'))

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

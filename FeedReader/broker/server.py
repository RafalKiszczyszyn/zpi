import http.server
import threading
from queue import Queue
from time import sleep


class BackgroundWorker:

    def __init__(self):
        self._queue = Queue()

    def work(self):
        print('Background worker started...')
        while True:
            tasks = self._queue.get(block=True)
            sleep(0.5)
            print('Started processing tasks in the background...')
            for task in tasks:
                task.execute()
            self._queue.task_done()
            print('Finished processing tasks.')

    def enqueue_work(self, tasks):
        self._queue.put(tasks)


background_worker = BackgroundWorker()


class HttpHandler(http.server.BaseHTTPRequestHandler):

    def __init__(self, endpoint, tasks, *args, **kwargs):
        self.endpoint = endpoint
        self.tasks = tasks
        # Base init must be called at the end.
        # It is because base init calls do_GET XDD
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == self.endpoint:
            background_worker.enqueue_work(self.tasks)
            self.send_response(200)
        else:
            self.send_response(404)


class HttpServer(http.server.HTTPServer):

    def __init__(self, base_address, port, endpoint, tasks):
        super(HttpServer, self).__init__(
            (base_address, port),
            lambda *args, **kwargs: HttpHandler(endpoint, tasks, *args, **kwargs))
        threading.Thread(target=background_worker.work).start()

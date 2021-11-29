import express from 'express';
import { Server } from 'http';

import config from './config';
import router from './routes';
import { ConsoleLogger } from './functions/logger';
import database_worker from './services/database-worker';
import event_worker from './services/event-worker';

const app = express();
app.use(router);

const start_service = () => {
	let server: Server;
	ConsoleLogger("Service prepering to start...");
	database_worker.connect()
		.then(() => app.use(router))
		.then(() => (server = app.listen(config.PORT)))
		.then(() => ConsoleLogger(`REST API started at http://localhost:${config.PORT}`))
		.then(() => event_worker.connect())
		.then(() => ConsoleLogger('Service successfully connected to RabbitMQ server'))
		.catch(async (err) => {
			ConsoleLogger("Stopped. Could not start service")
			await database_worker.close();
			server.close();
			setTimeout(() => start_service(), 30000)
			ConsoleLogger("Restarting in 30 seconds...")
		});
}

start_service();

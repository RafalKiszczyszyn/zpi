import express from 'express';
import config from './config';
import router from './routes';
import { ConsoleLogger } from './functions/logger';
import { initialize_connection } from './functions/database';
import start_event_consumer from './services/event-worker';

const app = express();
ConsoleLogger("Service prepering to start...");
initialize_connection()
	.then(() => app.use(router))
	.then(() => app.listen(config.PORT))
	.then(() => ConsoleLogger(`REST API started at http://localhost:${config.PORT}`))
	.then(() => start_event_consumer())
	.then(() => ConsoleLogger('Service successfully connected to RabbitMQ server'))
	.catch((err) => ConsoleLogger("Stopped. Could not start service"));
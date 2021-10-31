import express from 'express';
import config from './config';
import router from './routes';
import { ConsoleLogger } from './functions/logger';
import { initialize_connection } from './functions/database';
import event_consumer from './services/event-worker';

const app = express();
ConsoleLogger("Service prepering to start...");
event_consumer();
initialize_connection()
	.then(() => app.use(router))
	.then(() => app.listen(config.PORT))
	.then(() => ConsoleLogger(`Service started at http://localhost:${config.PORT}`))
	.catch((err) => ConsoleLogger("Could not start service"));
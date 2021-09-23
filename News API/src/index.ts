import express from 'express';
import config from './config';
import { ConsoleLogger } from './utils/loggers';
import { initializeConnection } from './utils/database';

const app = express();
const logger = ConsoleLogger("News API");

// TODO: There might be a problem if the application starts but the database failed to connection
// This situation can happen if either there is slow connection or database is down
// Don't know how to fix it yet, but it can be fixed in the future.
initializeConnection();

app.post('/events', (req: express.Request, res: express.Response) => {
	const event = req.body;
	switch (event.type) {
		case 'ArticleParsed':
			const article = req.body.article;
			logger("Saving parsed article to database...");
			logger(article.toString());

		case 'Ping':
			const payload = req.body.payload;
			logger("Ping event consumed. Payload: " + payload);
	}
	res.sendStatus(200);
});

app.listen(config.PORT, () => {
	logger(`Service started at http://localhost:${config.PORT}`);
});
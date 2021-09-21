import express from 'express';
import config from './config';
import { ConsoleLogger } from './utils';

const app = express();
const logger = ConsoleLogger("News API")

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
	logger(` Service started at http://localhost:${config.PORT}`);
});
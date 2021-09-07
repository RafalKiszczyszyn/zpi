const express = require('express');
const axios = require('axios');
const config = require('./config');
const { ConsoleLogger } = require('./loggers')

const app = express();
const consoleLogger = ConsoleLogger("EventBus")


app.use(express.json());

app.post('/events', (req, res) => {
	consoleLogger("Event recieved: " + req.body);

	const event = req.body;
	if (event.type === undefined || event.payload === undefined) {
		consoleLogger("Recieved event is incorrect");
	} else {
		config.URLS.map((url, index) => {
			consoleLogger("Emiting event to: " + url);
			axios
				.post(url, event)
				.catch(err => consoleLogger(err));
		})
	}
	res.sendStatus(200);
});

app.listen(config.PORT, (req, res) => {
	consoleLogger("Service listening on port: " + config.PORT);
});
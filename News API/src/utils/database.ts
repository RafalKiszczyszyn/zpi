import mongoose from 'mongoose';
import { ConsoleLogger } from './loggers';
import config from '../config';

const dbLogger = ConsoleLogger("News API -> DB")

export const initializeConnection = () => {
	mongoose
		.connect(config.DB)
		.then(() => dbLogger("Connection with database established successfully"))
		.catch((err) => dbLogger(err));

	mongoose.connection.on("error", (err) => dbLogger(err));
	mongoose.connection.on("disconnected", () => dbLogger("Connection with database closed"))
}
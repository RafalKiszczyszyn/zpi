import mongoose from 'mongoose';
import { ConsoleLogger } from './logger';
import config from '../config';

export const initialize_connection = async () => {
	try {
		await mongoose.connect(config.DB_URL)
		ConsoleLogger("Connection with database established successfully");
	} catch (err) {
		ConsoleLogger(err);
		throw err;
	}

	mongoose.connection.on("error", (err) => ConsoleLogger(err));
	mongoose.connection.on("disconnected", () => ConsoleLogger("Connection with database closed"));
}
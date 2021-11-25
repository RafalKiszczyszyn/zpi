import mongoose from 'mongoose';
import { ConsoleLogger } from '../functions/logger';
import config from '../config';

const connect = async () => {
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

const close = async () => {
	try {
		await mongoose.disconnect();
		mongoose.connection.removeAllListeners();
	} catch (err) {
		ConsoleLogger(err);
	}
}

export default {
	connect,
	close
}
import { Message } from 'amqplib';
import fs from 'fs';
import path from 'path';
import { IMessage } from '../models/message';

type ILogger = (message: string) => void;
type ILoggerFactory = (loggers: ILogger[]) => ILogger;

// Create a consistent logger message format
export const formatLogMessage = (message: string): string => {
	const date = new Date();
	const timestamp = `[${date.toLocaleDateString("en")} ${date.toLocaleTimeString("pl")}]`;
	return `${timestamp} (Articles API) ${message}`;
}

// Parse bytes array recieved from the RabbitMQ and return a message object
export const parseRabbitMessage: (msg:Message) => IMessage = (msg: Message) => {
	return JSON.parse(Buffer.from(msg.content).toString()) as IMessage;
}

// Logger that logs to standard output
export const ConsoleLogger: ILogger = (message: string) => {
	const formatedMessage = formatLogMessage(message);
	console.log(formatedMessage);
}

// TODO: This logger was not tested
// Logger that logs to file output
export const FileLogger: ILogger = (message: string) => {
	const formatedMessage = formatLogMessage(message);
	fs.appendFile(path.join(__dirname, `../../logs_${new Date().toLocaleDateString()}`), formatedMessage, (err) => {
		throw err;
	});
}

// Join multiple loggers into one logger that logs one message to multiple outputs
export const JoinedLoggerFactory: ILoggerFactory = (loggers: ILogger[]) => (message: string) => {
	const formatedMessage = formatLogMessage(message);
	loggers.forEach(logger => logger(formatedMessage));
}
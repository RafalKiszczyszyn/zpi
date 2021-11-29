import fs from 'fs';
import path from 'path';
import { formatLogMessage } from './utils';

type ILogger = (message: string) => void;
type ILoggerFactory = (loggers: ILogger[]) => ILogger;

export const ConsoleLogger: ILogger = (message: string) => {
	const formatedMessage = formatLogMessage(message);
	console.log(formatedMessage);
}

export const FileLogger: ILogger = (message: string) => {
	const formatedMessage = formatLogMessage(message);
	fs.appendFile(path.join(__dirname, `../../logs_${new Date().toLocaleDateString()}`), formatedMessage, (err) => {
		throw err;
	});
}

export const JoinedLoggerFactory: ILoggerFactory = (loggers: ILogger[]) => (message: string) => {
	const formatedMessage = formatLogMessage(message);
	loggers.forEach(logger => logger(formatedMessage));
}
import fs from 'fs';
import { format_log_message } from './utils';

type ILogger = (message: string) => void;
type ILoggerFactory = (loggers: ILogger[]) => ILogger;

export const ConsoleLogger: ILogger = (message: string) => {
	const formatedMessage = format_log_message(message);
	console.log(formatedMessage);
}

export const FileLogger: ILogger = (message: string) => {
	const formatedMessage = format_log_message(message);
}

export const JoinedLoggerFactory: ILoggerFactory = (loggers: ILogger[]) => (message: string) => {
	const formatedMessage = format_log_message(message);
	loggers.forEach(logger => logger(formatedMessage));
}
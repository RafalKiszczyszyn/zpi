import { Connection, Channel, connect, Replies, Message } from 'amqplib';
import config from '../config';
import { IMessage } from '../models/message';
import { ConsoleLogger, parseRabbitMessage } from '../utils';

type IConsumer = (channel: Channel) => (msg: Message | null) => void;
let connection: Connection;

const connectWorker = async (onConsume: IConsumer = defaultOnConsume) => {
	connection = await connect(config.RABBIT_URL);
	connection.on('error', (err) => console.log(err))
	
	const channel: Channel = await connection.createChannel();
	const queue: Replies.AssertQueue = await channel.assertQueue('scrapper.feed', { exclusive: true, durable: true });
	
	await channel.bindQueue(queue.queue, config.RABBIT_EXCHANGE_NAME, '');
	await channel.consume(queue.queue, onConsume(channel));
}

const disconnectWorker = () => {
	connection.removeAllListeners();
	connection.close();
}

const defaultOnConsume: IConsumer = (channel) => (msg) => {
	if (msg !== null) {
		let message: IMessage = parseRabbitMessage(msg);
		ConsoleLogger("Event recieved");
		ConsoleLogger(`Recived articles ${message.title}`);
		ConsoleLogger(`Recieved ${message.articles.length} articles`);
		channel.ack(msg);
	}
}

export default {
	connect: connectWorker,
	disconnect: disconnectWorker
}

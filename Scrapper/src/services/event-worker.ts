import { Connection, Channel, connect, Replies, Message } from 'amqplib';
import config from '../config';
import { IMessagePublished, IMessageRecieved } from '../models/message';
import { ConsoleLogger, parseRabbitMessage } from '../utils';

type IConsumer = (channel: Channel) => (msg: Message | null) => void;
let connection: Connection;
let publishChannel: Channel;

const connectConsumerWorker = async (onConsume: IConsumer = defaultOnConsume) => {
	ConsoleLogger(`Connecting to '${config.RABBIT.EXCHANGES.CONSUME}' exchange`)
	const channel: Channel = await connection.createChannel();
	const queue: Replies.AssertQueue = await channel.assertQueue('scrapper.feed', { exclusive: true, durable: true });
	
	await channel.bindQueue(queue.queue, config.RABBIT.EXCHANGES.CONSUME, '');
	await channel.consume(queue.queue, onConsume(channel));
}

const disconnectWorker = () => {
	ConsoleLogger("Disconectiong from RabbitMQ")
	connection.removeAllListeners();
	connection.close();
}

const defaultOnConsume: IConsumer = (channel) => (msg) => {
	if (msg !== null) {
		let message: IMessageRecieved = parseRabbitMessage(msg);
		ConsoleLogger("Event recieved");
		ConsoleLogger(`Recived articles ${message.title}`);
		ConsoleLogger(`Recieved ${message.articles.length} articles`);
		channel.ack(msg);
	}
}

const connectPublisherWorker = async () => {
	ConsoleLogger(`Connecting to '${config.RABBIT.EXCHANGES.PUBLISH}' exchange`)
	const channel = await connection.createChannel();
	await channel.assertExchange("scraps", "fanout", { durable: true, });
	publishChannel = channel;
}

const publish = (message: IMessagePublished) => {
	ConsoleLogger(`Publishing results to '${config.RABBIT.EXCHANGES.PUBLISH}' exchange`)
	publishChannel.publish(
		config.RABBIT.EXCHANGES.PUBLISH,
		'',
		Buffer.from(JSON.stringify(message)),
		{ persistent: true }
	);
}

const connectWorker = async (onConsume: IConsumer) => {
	ConsoleLogger("Creating connection with RabbitMQ")
	connection = await connect(config.RABBIT.URL);
	connection.on('error', (err) => console.log(err))

	await connectPublisherWorker();
	await connectConsumerWorker(onConsume);
}

export default {
	connect: connectWorker,
	disconnect: disconnectWorker,
	publish
}

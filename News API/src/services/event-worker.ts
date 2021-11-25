import { Connection, Channel, connect, Replies, Message } from 'amqplib';
import { IMessage } from '../models/article.model';
import { ConsoleLogger } from '../functions/logger';
import config from '../config'

const connect_worker = async () => {
	const connection: Connection = await connect(config.RABBIT_URL);
	connection.on('error', (err) => console.log(err))
	
	const channel: Channel = await connection.createChannel();
	const queue: Replies.AssertQueue = await channel.assertQueue('', { exclusive: true });
	
	await channel.bindQueue(queue.queue, config.RABBIT_EXCHANGE_NAME, '')
	await channel.consume(queue.queue, on_consume(channel));

}

const on_consume = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessage = parse_message(msg);
		ConsoleLogger("Event recieved");
		ConsoleLogger(`Recived articles from ${message.title}`);
		ConsoleLogger(`Recieved ${message.articles.length} articles`);
		channel.ack(msg);
	}
}

const parse_message = (msg: Message) => {
	return JSON.parse(Buffer.from(msg.content).toString())
}

export default {
	connect: connect_worker
}

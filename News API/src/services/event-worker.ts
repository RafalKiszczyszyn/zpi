import { Connection, Channel, connect, Replies, Message } from 'amqplib/callback_api';
import { ConsoleLogger } from '../functions/logger';

type Error = any;

const bail = (err: Error) => {
	ConsoleLogger(err);
	process.exit(1);
}

const on_consume = (channel: Channel) =>
{
	let counter = 0;
	return (msg: Message | null) => {
		if (msg !== null) {
			ConsoleLogger("Event recieved: " + counter);
			counter++;
			channel.ack(msg);
		}
	}
}

const on_assert_queue = (err: Error, queue_reply: Replies.AssertQueue, channel: Channel) => {
	if (err !== null) bail(err);

	channel.bindQueue(queue_reply.queue, "logs", '');
	channel.consume(queue_reply.queue, on_consume(channel));
}

const on_consumer_open = (err: Error, channel: Channel) => {
	if (err != null) bail(err);
	channel.assertQueue('', { exclusive: true }, (assert_error, q_reply) => on_assert_queue(assert_error, q_reply, channel));
}

const consumer = (conn: Connection) => {
	conn.createChannel(on_consumer_open);
}

// TODO: Configurable queue name
export default () => {
	connect("amqp://localhost", (err: Error, conn: Connection) => {
		if (err != null) bail(err);
		consumer(conn);
	});
}
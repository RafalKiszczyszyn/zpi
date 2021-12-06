import { Connection, Channel, connect, Replies, Message } from 'amqplib';
import { IArticle, IMessageFeed, IMessageScrapps } from '../models/article.model';
import { ConsoleLogger } from '../functions/logger';
import config from '../config'
import { CreateArticle, UpdateArticleContent } from '../controllers/article.controller';

const connect_worker = async () => {
	ConsoleLogger("Rabbit url: " + config.RABBIT.URL);
	const connection: Connection = await connect(config.RABBIT.URL);
	connection.on('error', console.log)
	
	// Feed Channel
	const feedChannel: Channel = await connection.createChannel();
	const { queue: feedQueue }: Replies.AssertQueue
		= await feedChannel.assertQueue(config.RABBIT.QUEUE.FEED, { exclusive: true, durable: true });
	
	await feedChannel.bindQueue(feedQueue, config.RABBIT.EXCHANGE.FEED, '')
	await feedChannel.consume(feedQueue, onConsumeFeed(feedChannel));

	// Scrapper channel
	const scrapperChannel: Channel = await connection.createChannel();
	const { queue: scrapperQueue }: Replies.AssertQueue
		= await scrapperChannel.assertQueue(config.RABBIT.QUEUE.SCRAPS, { exclusive: true, durable: true });

	await scrapperChannel.bindQueue(scrapperQueue, config.RABBIT.EXCHANGE.SCRAPS, '');
	await scrapperChannel.consume(scrapperQueue, onConsumeScraps(scrapperChannel))
}

const onConsumeFeed = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessageFeed = parse_message(msg);
		ConsoleLogger(`Recived ${message.articles.length} articles from ${message.title}`);
		let articles: IArticle[] = [...message.articles];
		articles.forEach(article => CreateArticle(article));
		channel.ack(msg);
	}
}

const onConsumeScraps = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessageScrapps = parse_message(msg);
		ConsoleLogger(`Recived ${message.articles.length} articles from ${message.title}`);
		let articles = [...message.articles];
		articles.forEach(article => UpdateArticleContent(article));
		channel.ack(msg);
	}
}

const onConsumeSentiments = (channel: Channel) => (msg: Message | null) => {
	ConsoleLogger('Nothing here yet');
}
const parse_message = (msg: Message) => {
	return JSON.parse(Buffer.from(msg.content).toString())
}

export default {
	connect: connect_worker
}

import { Connection, Channel, connect, Replies, Message } from 'amqplib';
import { IArticle, IMessageFeed, IMessageScrapps } from '../models/article.model';
import { ConsoleLogger } from '../functions/logger';
import config from '../config'
import { CreateArticle, UpdateArticleContent, UpdateArticleSentiments } from '../controllers/article.controller';
import { IMessageSentiments, ISegement } from '../models/message.model';

const connect_worker = async () => {

	const {
		PROTOCOL,
		USER,
		PASSWORD,
		HOST,
		VHOST,
	} = config.RABBIT.CONNECTION;
	const connectionString = `${PROTOCOL}://${USER}:${PASSWORD}@${HOST}/${VHOST}`
	const connection: Connection = await connect(connectionString);
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
	await scrapperChannel.consume(scrapperQueue, onConsumeScraps(scrapperChannel));
	
	// Scrapper channel
	const sentimentChannel: Channel = await connection.createChannel();
	const { queue: sentimentQueue }: Replies.AssertQueue
		= await sentimentChannel.assertQueue(config.RABBIT.QUEUE.SENTIMENTS, { exclusive: true, durable: true });

	await sentimentChannel.bindQueue(sentimentQueue, config.RABBIT.EXCHANGE.SENTIMENTS, '');
	await sentimentChannel.consume(sentimentQueue, onConsumeSentiments(sentimentChannel));
}

const onConsumeFeed = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessageFeed = parse_message(msg);
		ConsoleLogger(`Recived ${message.articles.length} articles from feed`);
		let articles: IArticle[] = [...message.articles];
		articles.forEach(article => CreateArticle(article));
		channel.ack(msg);
	}
}

const onConsumeScraps = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessageScrapps = parse_message(msg);
		ConsoleLogger(`Recived ${message.articles.length} articles from scraps`);
		let articles = [...message.articles];
		articles.forEach(article => UpdateArticleContent(article));
		channel.ack(msg);
	}
}

const onConsumeSentiments = (channel: Channel) => (msg: Message | null) => {
	if (msg !== null) {
		let message: IMessageSentiments = parse_message(msg);

		ConsoleLogger(`Recived message from sentiments`);
		message.forEach(segment => UpdateArticleSentiments({
			guid: segment.id,
			sentiment_content: segment.segment == 'content' ? segment.polarity : undefined,
			sentiment_title: segment.segment == 'title' ? segment.polarity : undefined,
			sentiment_summary: segment.segment == 'summary' ? segment.polarity : undefined,
		}));
		channel.ack(msg);
	}
}
const parse_message = (msg: Message) => {
	return JSON.parse(Buffer.from(msg.content).toString())
}

export default {
	connect: connect_worker
}

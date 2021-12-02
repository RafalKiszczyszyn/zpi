import Scrapper from "./services/scrapper";
import EventWorker from "./services/event-worker";
import { ConsoleLogger, parseRabbitMessage } from "./utils";
import { Channel, Message } from "amqplib";
import { IMessagePublished, IMessageRecieved } from "./models/message";

const onConsume = (channel: Channel) => async (message: Message | null) => {
	const defaultNodes = [
		'.news__description > p',
	]
	if (message != null) {
		const parsedMessage: IMessageRecieved = parseRabbitMessage(message);
		const contentNodes = parsedMessage.contentNodes || defaultNodes;
		const articles = await Promise.all(parsedMessage.articles.map(async (article) => {
			const { link, guid } = article;
			const content = await Scrapper.scrapeSite(link, contentNodes);
			return { guid, content };
		}));
		channel.ack(message);

		const resultMessage: IMessagePublished = {
			...parsedMessage,
			articles
		}
		EventWorker.publish(resultMessage);
	}
}

const startService = async () => {
	try {
		await EventWorker.connect(onConsume);
	} catch (e) {
		ConsoleLogger("Service could not start");
		EventWorker.disconnect();
		setTimeout(() => startService(), 30000);
		ConsoleLogger("Restarting in 30 seconds...");
	}
}

startService();
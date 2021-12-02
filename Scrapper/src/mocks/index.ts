import { IMessageRecieved } from "../models/message"

const RabbitMessage: IMessageRecieved = {
	title: 'Example title',
	updated: new Date(),
	lang: 'en',
	contentNodes: [
		'.news__description > p',
	],
	articles: [
		{
			guid: '1',
			title: 'Example title 1',
			summary: 'Example summary 1',
			published: new Date(),
			updated: new Date(),
			link: 'https://www.polsatnews.pl/wiadomosc/2021-11-07/ryszard-czarnecki-uhonorowany-przez-uniwersytet-zostal-doctor-honoris-causa-w-uzbekistanie/',
		},
		{
			guid: '2',
			title: 'Example title 2',
			summary: 'Example summary 2',
			published: new Date(),
			updated: new Date(),
			link: 'https://www.polsatnews.pl/wiadomosc/2021-11-14/brytyjskie-msz-apeluje-o-zablokowanie-nord-stream-2-chce-aby-nasi-przyjaciele-do-nas-dolaczyli',
		},
		{
			guid: '3',
			title: 'Example title 3',
			summary: 'Example summary 3',
			published: new Date(),
			updated: new Date(),
			link: 'https://www.polsatnews.pl/wiadomosc/2021-11-14/szefowa-brytyjskiego-msz-o-kryzysie-na-granicy-wielka-brytania-nie-bedzie-odwracac-wzroku/'
		}
	]
}

export {
	RabbitMessage
}
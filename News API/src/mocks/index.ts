import Article, { IArticle, IMessageFeed, IMessageScrapps } from '../models/article.model';

const article: IArticle = new Article({
	title: 'Ryszard Czarnecki uhonorowany przez uniwersytet. Został doctor honoris causa w Uzbekistanie',
	summary: 'Europoseł PiS Ryszard Czarnecki został uhonorowany przez University of World Economy and Dyplomacy w Taszkiencie (Uzbekistan). Polityk otrzymał od uczelni doktorat honoris causa za znaczący wkład w partnerstwo strategiczne i stosunki dyplomatyczne oraz wzmacnianie obustronnych relacji i przyjaźni między Republiką Uzbekistanu a UE. Zdjęcia z oficjalnej uroczystości obiegły sieć.',
	published: new Date('2021-11-07T12:20:00'),
	updated: new Date('2021-11-07T12:20:00'),
	link: 'https://www.polsatnews.pl/wiadomosc/2021-11-07/ryszard-czarnecki-uhonorowany-przez-uniwersytet-zostal-doctor-honoris-causa-w-uzbekistanie/',
	guid: 'https://www.polsatnews.pl/wiadomosc/2021-11-07/ryszard-czarnecki-uhonorowany-przez-uniwersytet-zostal-doctor-honoris-causa-w-uzbekistanie/',
	enclosures: [
		{
			link: 'https://www.polsatnews.pl/image/mini/1610435.jpg',
			length: 22603,
			type: 'image/jpg'
		},
		{
			link: 'https://ipla.pluscdn.pl/dituel/cp/sy/syr8bjv2by1y3bmqh39edj1uvhq52dmt.jpg',
			length: 72161,
			type: 'image/jpg'
		},
	],
});

export const MessageFeed: IMessageFeed = {
	title: 'Polsat News - Wiadomości - Polska',
	updated: new Date('2021-11-07T12:40:37'),
	lang: 'pl',
	articles: [ article ],
};

export const MessageScrapps: IMessageScrapps = {
	title: 'Polsat News - Wiadomości - Polska',
	updated: new Date('2021-11-07T12:40:37'),
	lang: 'pl',
	articles: [ { guid: article.guid, content: 'Mocked content.Mocked content.Mocked content.Mocked content.'} ],
};
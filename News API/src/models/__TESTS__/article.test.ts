import DatabaseWorker from '../../services/database-worker';
import Article, { IArticleModel } from '../article.model';

describe("Article model", () => {
	beforeAll(async () => {
		await DatabaseWorker.connect();
	});

	afterAll(async () => {
		await DatabaseWorker.close();
	});

	it("Should throw validation errors", () => {
		const article = new Article();
		expect(article.validate).toThrow();
	});

	it("Should save a article", async () => {
		expect.assertions(4);

		const article: IArticleModel = new Article({
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
				}
			],
		});

		const saveSpy = jest.spyOn(article, "save");
		await article.save();

		expect(saveSpy).toHaveBeenCalled();

		expect(article).toMatchObject({
			title: expect.any(String),
			summary: expect.any(String),
			published: expect.any(Date),
			updated: expect.any(Date),
			link: expect.any(String),
			guid: expect.any(String),
			enclosures: expect.any(Array),
		});
		expect(article.enclosures.length).toBeGreaterThan(0);
		expect(article.guid).toBe('https://www.polsatnews.pl/wiadomosc/2021-11-07/ryszard-czarnecki-uhonorowany-przez-uniwersytet-zostal-doctor-honoris-causa-w-uzbekistanie/');
	});
});
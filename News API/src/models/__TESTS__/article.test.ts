import mongoose from 'mongoose';
import { initializeConnection } from '../../functions/utils/database';
import Article, { IArticle } from '../article.model';
import config from '../../config';


describe("Article model", () => {
	beforeAll(async () => {
		initializeConnection();
	});

	afterAll(async () => {
		await mongoose.connection.close();
	});

	it("Should throw validation errors", () => {
		const article = new Article();
		expect(article.validate).toThrow();
	});

	it("Should save a article", async () => {
		expect.assertions(3);

		const article: IArticle = new Article({
			title: "Example title",
			description: "Example description",
			datePublished: new Date(),
			source: {
				id: "example_source",
				name: "Example Source",
				url: "https://www.example.com/",
			},
			characteristics: true,
		});

		const saveSpy = jest.spyOn(article, "save");
		await article.save();

		expect(saveSpy).toHaveBeenCalled();

		expect(article).toMatchObject({
			title: expect.any(String),
			description: expect.any(String),
			datePublished: expect.any(Date),
			source: {
				id: expect.any(String),
				name: expect.any(String),
				url: expect.any(String),
			},
			characteristics: expect.any(Boolean),
		});

		expect(article.source.id).toBe("example_source");
	});
});
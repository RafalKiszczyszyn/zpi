import mongoose from 'mongoose';
import { initialize_connection } from '../../functions/database';
import { CreateArticle } from '../article.controller';
import Article from '../../models/article.model'
import config from '../../config';


describe("Article controller", () => {
	beforeAll(async () => {
		initialize_connection();
	});

	afterAll(async () => {
		await mongoose.connection.close();
	});

	it("Should create article", async () => {
		const testArticle = new Article({
			title: "Test Article",
			description: "Test Description",
			datePublished: new Date(),
			characteristics: false,
			source: {
				id: "test_id",
				name: "Test Name",
				url: "https://www.example.com/"
			}
		});

		const result = await CreateArticle(testArticle);

		expect(result.source.id).toBe("test_id");
	});
});
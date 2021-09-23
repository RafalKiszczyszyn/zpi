import mongoose from 'mongoose';
import { initializeConnection } from '../../utils/database';
import Article, { IArticle } from '../article.model';
import config from '../../config';

beforeAll(async () => {
	initializeConnection();
});

afterAll(async () => {
	await mongoose.connection.close();
});

describe("Article model", () => {
	it("Should throw validation errors", () => {
		const article = new Article();
		expect(article.validate).toThrow();
	});
});
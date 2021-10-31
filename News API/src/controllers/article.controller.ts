import Article, { IArticle } from '../models/article.model';

interface IArticleQueryParams {
	before?: string;
	after?: string;
	query?: string;
}

export async function CreateArticle({
	title,
	description,
	datePublished,
	source,
	characteristics
}: IArticle): Promise<IArticle> {
	const article = new Article({ title, description, datePublished, source, characteristics });
	const data = await article.save();
	return data;
}

export async function QueryArticles({
	before,
	after,
	query
}: IArticleQueryParams): Promise<IArticle[]> {
	const articles: IArticle[] = await Article.find({});
	return articles;
}
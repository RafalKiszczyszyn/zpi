import Article, { IArticle } from '../models/article.model';

interface IArticleQueryParams {
	before?: string;
	after?: string;
	query?: string;
}

export async function CreateArticle(article: IArticle): Promise<IArticle> {
	const data = await Article.findOneAndUpdate(
		{ guid: article.guid }, 
		{ ...article },
		{ upsert: true, new: true, setDefaultsOnInsert: true }
	);
	return data;
}

export async function UpdateArticle(article: IArticle): Promise<IArticle> {
	const data = await Article.findOneAndUpdate({ guid: article.guid }, { ...article });
	return data;
}

export async function UpdateArticleContent({
	content,
	guid,
}: { content: string, guid: string }): Promise<IArticle> {
	const data = await Article.findOneAndUpdate({ guid }, { content });
	return data;
}

interface ISegment {
	guid: string;
	sentiment_title?: number;
	sentiment_description?: number;
	sentiment_content?: number;
}

export async function UpdateArticleSentiments(segment: ISegment): Promise<IArticle> {
	const data = await Article.findOneAndUpdate({ guid: segment.guid }, { ...segment });
	return data;
}

export async function QueryArticles({
	before,
	after,
	query
}: IArticleQueryParams): Promise<IArticle[]> {
	const gtDate = after ? new Date(after) : new Date(0);
	const ltDate = before ? new Date(before) : new Date();
	const qRegex = query ? query : "";

	const articles: IArticle[] = await Article.find({
		datePublished: {
			$gt: gtDate,
			$lt: ltDate,
		},
		$or: [{ description: { $regex: qRegex } }, { title: { $regex: qRegex } }, { content: { $regex: qRegex } }]
	});
	return articles;
}

export async function QueryArticle(uuid: string): Promise<IArticle> {
	const article: IArticle = await Article.findById(uuid);
	return article;
}

export default {
	CreateArticle,
	QueryArticle,
	QueryArticles,
	UpdateArticle,
	UpdateArticleContent,
	UpdateArticleSentiments
};
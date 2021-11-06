import Article, { IArticle } from '../models/article.model';

interface IArticleQueryParams {
	before?: string;
	after?: string;
	query?: string;
}

export async function CreateArticle({
	title,
	summary,
	published,
	updated,
	link,
	guid,
	enclosures
}: IArticle): Promise<IArticle> {
	const article = new Article({ title, summary, published, updated, link, guid, enclosures });
	const data = await article.save();
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
		$or: [{ description: { $regex: qRegex } }, { title: { $regex: qRegex } }]
	});
	return articles;
}

export async function QueryArticle(uuid: string): Promise<IArticle> {
	const article: IArticle = await Article.findById(uuid);
	return article;
}

export default { CreateArticle, QueryArticles, QueryArticle };
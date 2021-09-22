import Article, { IArticle } from '../models/article.model';

// TODO: This is not tested
export async function CreateArticle({
	title,
	description,
	datePublished,
	source,
	characteristics
}: IArticle): Promise<IArticle> {
	return new Article({ title, description, datePublished, source, characteristics })
		.save()
		.then((data) => { return data })
		.catch((err) => { throw err });
}
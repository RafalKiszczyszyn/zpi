import Article, { IArticle } from '../models/article.model';

async function CreateArticle({
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

export default {
	CreateArticle
}
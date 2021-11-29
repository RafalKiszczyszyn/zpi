import mongoose, { Schema, Document } from 'mongoose';

export interface IEnclosure {
	link: string,
	length: number,
	type: string,
}

export interface IArticle {
	title: string,
	summary: string,
	content?: string,
	published: Date,
	updated: Date,
	link: string,
	guid: string,
	enclosures: Array<IEnclosure>,
	sentiment_title?: number,
	sentiment_summary?: number,
	sentiment_content?: number,
	data_complete: boolean,
}

export type IArticleModel = IArticle & Document;
export interface IMessageFeed {
	title: string,
	updated: Date,
	lang: string,
	articles: Array<IArticle>,
}
export interface IMessageScrapps {
	title: string,
	updated: Date,
	lang: string,
	articles: Array<{guid: string, content: string}>,
}

const ArticleSchema: Schema = new Schema({
	title: { type: String, required: true },
	summary: { type: String, required: true },
	content: { type: String, required: false },
	published: { type: Date, required: true },
	updated: { type: Date, required: true },
	link: { type: String, required: true },
	guid: { type: String, required: true },
	enclosures: [{
		link: { type: String, required: true },
		length: { type: Number, required: true },
		type: { type: String, required: true }
	}],
	sentiment_title: { type: Number, required: false },
	sentiment_summary: { type: Number, required: false },
	sentiment_content: { type: Number, required: false },
}, { collection: "Articles" });

export default mongoose.model<IArticle>('Article', ArticleSchema);
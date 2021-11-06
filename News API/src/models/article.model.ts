import mongoose, { Schema, Document } from 'mongoose';

export interface IEnclosure {
	link: string,
	length: number,
	type: string,
}

export interface IArticle extends Document {
	title: string,
	summary: string,
	published: Date,
	updated: Date,
	link: string,
	guid: string,
	enclosures: Array<IEnclosure>,
	sentiment?: boolean,
}

export interface IMessage {
	title: string,
	updated: Date,
	lang: string,
	articles: Array<IArticle>,
}

const ArticleSchema: Schema = new Schema({
	title: { type: String, required: true },
	summary: { type: String, required: true },
	published: { type: Date, required: true },
	updated: { type: Date, required: true },
	link: { type: String, required: true },
	guid: { type: String, required: true },
	enclosures: [{
		link: { type: String, required: true },
		length: { type: Number, required: true },
		type: { type: String, required: true }
	}],
	sentiment: { type: Boolean, required: false },
}, { collection: "Articles" });

export default mongoose.model<IArticle>('Article', ArticleSchema);
import mongoose, { Schema, Document } from 'mongoose';

export interface ISource extends Document {
	id: string,
	name: string,
	url: string,
}

export interface IArticle extends Document {
	title: string,
	description: string,
	datePublished: Date,
	source: ISource
	characteristics?: boolean,
}

const ArticleSchema: Schema = new Schema({
	title: { type: String, required: true },
	description: { type: String, required: true },
	datePublished: { type: Date, required: true },
	source: {
		id: { type: String, required: true },
		name: { type: String, required: true },
		url: { type: String, required: true },
	},
	characteristics: { type: Boolean, required: true },
}, { collection: "Articles" });

export default mongoose.model<IArticle>('Article', ArticleSchema);
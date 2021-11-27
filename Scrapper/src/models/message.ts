import { IArticle } from './article';

export interface INode {
	tag: string,
	classes: Array<string>,
	children: Array<INode>
}

export interface IMessage {
	title: string,
	updated: Date,
	lang: string,
	contentNodes: Array<string>,
	articles: Array<IArticle>
}
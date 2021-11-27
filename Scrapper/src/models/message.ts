import { IArticle } from './article';

export interface INode {
	tag: string,
	classes: Array<string>,
	children: Array<INode>
}

export interface IMessageRecieved {
	title: string,
	updated: Date,
	lang: string,
	contentNodes: Array<string>,
	articles: Array<IArticle>
}

export interface IMessagePublished {
	title: string,
	updated: Date,
	lang: string,
	articles: Array<{guid: string, content: string}>
}
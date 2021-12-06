export interface ISegement {
	id: string; // GUID of articles
	segment: 'title' | 'summary' | 'content'; // Type of segement which the sentiment was calculated for
	polarity: number; // Float [-1, 1]
}

export type IMessageSentiments = Array<ISegement>;
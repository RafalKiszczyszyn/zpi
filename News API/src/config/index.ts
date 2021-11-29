export default {
	PORT: 4010,
	DB: {
		URL: "mongodb+srv://backend:backend@cluster0.pifu7.mongodb.net/ArticlesClassificationSystem?retryWrites=true&w=majority",
	},
	RABBIT: {
		EXCHANGE: {
			FEED: "feed",
			SCRAPS: 'scraps',
			SENTIMENTS: 'sentiments'
		},
		QUEUE: {
			FEED: "articles.feed",
			SCRAPS: 'articles.scraps',
			SENTIMENTS: 'articles.sentiments'
		},
		URL: "amqp://guest:guest@localhost",
	}
}
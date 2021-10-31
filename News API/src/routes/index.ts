import { Router } from 'express';
import { QueryArticles } from '../controllers/article.controller';
import { ConsoleLogger } from '../functions/logger';
import { parse_query_string } from '../functions/utils'
const router = Router();

router.get('/articles', async (req, res) => {
	ConsoleLogger("GET articles");

	// Get params for this query
	// Date in ISO string like 2021-12-24T09:34:54
	const queryParams = parse_query_string(req.query);

	// Get articles from database
	const articles = await QueryArticles(queryParams);

	// Send them back
	res.send(articles).status(200);
});

export default router;
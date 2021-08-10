import express from 'express';
import config from './config';
import { Log } from './utils';
import { graphqlHTTP } from 'express-graphql';
import { Schema } from './graphql/schemas';

const app = express();

app.use("/api/graphql", graphqlHTTP({
	schema: Schema,
	graphiql: true,
}));

app.get("/", (req, res) => {
	res.send("<h1>Facade service working</h1>");
});

app.listen(config.PORT, () => {
	Log(`Server started at http://localhost:${config.PORT}`);
});

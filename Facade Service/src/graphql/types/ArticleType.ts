import { GraphQLBoolean, GraphQLObjectType, GraphQLString } from "graphql";

export const ArticleType = new GraphQLObjectType({
	name: "Article",
	fields: () => ({
		id: { type: GraphQLString },
		title: { type: GraphQLString },
		sourceUrl: { type: GraphQLString },
		sourceName: { type: GraphQLString },
		characteristic: { type: GraphQLBoolean },
	}),
});
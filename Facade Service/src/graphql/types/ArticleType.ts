import { GraphQLBoolean, GraphQLFloat, GraphQLObjectType, GraphQLString } from "graphql";

export const ArticleType = new GraphQLObjectType({
	name: "Article",
	fields: () => ({
		id: { type: GraphQLString },
		title: { type: GraphQLString },
		description: { type: GraphQLString },
		datePublished: { type: GraphQLFloat },
		imageURL: { type: GraphQLString },
		sourceUrl: { type: GraphQLString },
		sourceName: { type: GraphQLString },
		sourceId: { type: GraphQLString },
		characteristic: { type: GraphQLBoolean },
	}),
});
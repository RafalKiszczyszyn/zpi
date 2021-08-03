import {
	GraphQLList,
	GraphQLObjectType,
	GraphQLString,
} from "graphql";

import { repository } from "../../mock/article";
import { ArticleType } from "../types/ArticleType";

export const RootQuery = new GraphQLObjectType({
	name: "RootQuery",
	fields: () => ({
		ping: {
			type: GraphQLString,
			resolve: () => "GraphQL service working.",
		},
		articles: {
			type: GraphQLList(ArticleType),
			resolve: () => repository,
		}
	}),
});
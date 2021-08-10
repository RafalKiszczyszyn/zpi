import {
	GraphQLList,
	GraphQLObjectType,
	GraphQLString,
} from "graphql";
import { Log } from "../../utils";

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
			args: {
				id: { type: GraphQLString }
			},
			resolve: (source, { id }) => id !== undefined ? repository.filter(v => v.id.toString() === id.toString()) : repository,
			description: "If id was not found in repository, returns empty array. If id is not specified, returns all articles."
		}
	}),
});
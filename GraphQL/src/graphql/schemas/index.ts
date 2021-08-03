import { GraphQLSchema } from "graphql";
import { RootQuery } from "./rootQuery";

export const Schema = new GraphQLSchema({
	query: RootQuery,
});
import { Article } from '../types';
import { readFileSync } from "fs";
export const repository: Article[] = (() => {
	const jsonString = readFileSync("article_mock.json");
	const items = JSON.parse(jsonString.toString());
	return items;
})();


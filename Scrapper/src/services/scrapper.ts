import axios from 'axios';
import cheerio from 'cheerio';

export const sanitizeString = (value: string) => {
	// Replace multiple spaces, end of lines and tabs with one space. 
	const result = value.replace(/\s\s+/g, ' ');
	return result;
}

export const rawIntoText = ($: cheerio.Root, element: cheerio.Cheerio) => {
	return $(element).clone().children().remove().end().text();
}

export const reduceNodes = (prev: string, curr: string) => {
	if (!!curr.trim().length)
		return prev + curr
	else
		return prev
}

export async function scrapeSite(url: string, nodes: string[]): Promise<string> {
	try {
		// Get html from the link,
		const html_response = (await axios(url)).data;
		const $ = cheerio.load(html_response);
		const descriptionsRaw = nodes.map(value => $(value));

		const descriptions = descriptionsRaw.map(el => rawIntoText($, el));
		const description = descriptions.reduce(reduceNodes, "");

		return sanitizeString(description);
	} catch (err) {
		console.log(err)
		return '';
	}
}

export default {
	scrapeSite
}
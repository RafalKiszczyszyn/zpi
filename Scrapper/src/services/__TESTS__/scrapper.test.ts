import { rawIntoText, reduceNodes, sanitizeString, scrapeSite } from '../scrapper';
import { descriptions, exampleSite, exampleSiteContent, html } from '../../mocks/scrapper';
import cheerio from 'cheerio'
describe("Scrapper service", () => {
	it("Should reduce an array of nodes to one string", () => {
		expect.assertions(8);

		expect(reduceNodes("one", "two")).toEqual("onetwo");
		expect(reduceNodes("two", " three")).toEqual("two three");
		expect(reduceNodes("two", " ")).toEqual("two");
		expect(reduceNodes("two ", " ")).toEqual("two ");
		expect(reduceNodes("two", "")).toEqual("two");
		expect(reduceNodes("", " three")).toEqual(" three");
		expect(reduceNodes(" ", " three")).toEqual("  three");
		expect(descriptions.reduce(reduceNodes, "")).toEqual("One  on one two twoTwo")
	});

	it("Should sanitize string", () => {
		expect.assertions(3);

		expect(sanitizeString(descriptions.join(' '))).toEqual("One on one two two Two")
		expect(sanitizeString(" ")).toEqual(" ");
		expect(sanitizeString("     ")).toEqual(" ");
	});

	it("Should turn raw nodes into strings", () => {
		const $ = cheerio.load(html);
		const element = $('p')
		const sanatized = sanitizeString(rawIntoText($, element));
		expect(sanatized).toEqual("My first paragraph. DDD BBB CCC ");
	});

	it("Should scrape example site", async() => {
		const scrapedExample = await scrapeSite(exampleSite.url, exampleSite.nodes);
		expect(scrapedExample).toEqual(exampleSiteContent);

		const failedExample = await scrapeSite("not_good_url", ['p']);
		expect(failedExample).toEqual('');
	})
});
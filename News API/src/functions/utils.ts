export const parseQueryString = (queryString: any) => {
	const before = !!queryString._before && queryString._before.toString();
	const after = !!queryString._after && queryString._after.toString();
	const query = !!queryString._query && queryString._query.toString();
	return { before, after, query } 
}

export const formatLogMessage = (message: string): string => {
	const date = new Date();
	const timestamp = `[${date.toLocaleDateString("en")} ${date.toLocaleTimeString("pl")}]`;
	return `${timestamp} (Articles API) ${message}`;
}

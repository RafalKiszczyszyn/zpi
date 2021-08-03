export const Log = (message: string, name: string = "Facade") => {
	const datetime = new Date();
	// tslint:disable-next-line:no-console
	console.log(`${datetime.toISOString()} ${name.toUpperCase()}: ${message}`);
}
// TODO: Refactor
export const ConsoleLogger = (serviceName: string) => {
	return (message: string) => {
		const date = new Date();
		const timestamp = `[${date.toLocaleDateString("en")} ${date.toLocaleTimeString("pl")}]`
		console.log(`${timestamp} (${serviceName}) ${message}`)
	}
}
// TODO: Refactor
module.exports = {
	ConsoleLogger: (serviceName) => {
		return (message) => {
			const date = new Date();
			const timestamp = `[${date.toLocaleDateString("en")} ${date.toLocaleTimeString("pl")}]`
			console.log(`${timestamp} (${serviceName}) ${message}`)
		}
	}
}
# Event Bus
This is implementation of bus that distributes all events in the system. Every time one service emits an event, all interested parties will be notified. Interested services should have a POST /events endpoint. This endpoint will be used by event bus to notify about new events.

# Running
To run event bus:
	- npm install
	- npm start / npm run dev
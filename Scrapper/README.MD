# Scrapper
## Instalation
### Build service image
```
docker build -t scrapper .
```
### Run container
This service depends on exsistance of feed exchange. Before running the service the exchange should be created. This can be done either by running the FeedReader service or by creating durable feed exchange any other way.

- -d is a detached container, meaning it will not block the shell
- --network host makes sure that the container has all necessary network connectivity with other containers
```
docker run -d --hostname articles --name Articles --network host articles:latest
```
## Testing 
Test are run automaticaly by github actions. If you want to run the tests manualy you can use npm command
```
npm test
```
This will run all existing tests and create coverage raport. Raport can be found in _/coverage_ folder after tests have finished execution. 
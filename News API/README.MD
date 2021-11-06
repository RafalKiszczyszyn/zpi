# Articles API 
## Instalation
### Build service image
```
docker build -t articles .
```
### Run container
Before running the container be sure to run RabbitMQ and publisher services (FeedReader and NLPService). This part is critical since the service will not work if the message exchanges are not available.

- -d is a detached container, meaning it will not block the shell
- --network host makes sure that the container has all necessary network connectivity with other containers
```
docker run -d --hostname articles --name Articles --network host articles:latest
```
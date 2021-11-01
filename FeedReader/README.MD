## Broker
### ***How to install***
To create docker image run:
```
docker build -t feedreader .
```
Then start new container with command:
```
docker -d run --hostname feedreader --name FeedReader --network=host feedreader:latest
```
### ***How to run***
Connect to container's terminal and run command:
```
python app.py
```
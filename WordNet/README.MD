## WordNet
#### How to install
Build docker image from repository root:
```shell script
docker build -t wordnet -f /WordNet/Dockerfile .
```

Create docker container with command:
```shell script
docker run -d --hostname wordnet --name WordNet --network host wordnet:latest
```
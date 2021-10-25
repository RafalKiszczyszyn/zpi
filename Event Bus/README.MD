# Instalation
## How to install
Pull the newest RabbitMQ image from docker repo:
```
docker pull rabbitmq:latest
```

Build an image from Dockerfile:
```
docker build -t "rabbitmq-img" .
```

Create container:
```
docker run -d --hostname main --name Rabbito -p 15672:15672 -p 5672:5672 -p 5671:5671 -p 15671:15671 rabbitmq-img:latest
```

***Notice***

`./ssl` contains sample certificates and should be replaced with valid certificates on production environment.

# SSL
## How to generate self-signed certificate
Generate private key with RSA:
```
openssl genrsa -des3 -out <root-key-name>.key 2048
```

Generate CA with private key:
```
openssl req -x509 -new -nodes -key <key-name>.key -sha256 -out <ca-name>.pem
```

Generate certificate signing request CSR for peer:
```
openssl req -new -key <peer-key-name>.key -out <peer-name>.csr
```

Generate certificate CRT for peer:
```
openssl x509 -req -in <peer-name>.csr -CA <ca-name>.pem -CAkey <root-key-name>.key -CAcreateserial -out <peer-name>.crt -days 3600 -sha256
```

# Additional configuration
## Access control
Permissions are split into three categories: `configure`, `write` and `read`. Every operation on a resource requires one or more permission categories. For example:
```
Operation                   | Configure | Write    | Read     |
---------------------------------------------------------------
Create/Delete Exchange      | exchange  | -------- | -------- |
Create/Delete Queue         | queue     | -------- | -------- |
Bind/Unbind Queue           | --------- | queue    | exchange |
Publish                     | --------- | exchange | -------- |
Consume                     | --------- | -------- | queue    |
```
Default permissions for roles:
```
Publisher - '^(exchange)$' '^(exchange)$' '^$'
```
It means that publisher is allowed to create/delete exchange and publish messages on it.
```
Consumer - '^(queue)$' '^(queue)$' '^(exchange|queue)$'
```
It means that consumer is allowed to create/delete queues, bind/unbind those queues to exchange and read meassages from them.

## Virtual hosts
Virtual hosts are used to logically separate server structure. There are two virtual hosts in the system: `/articles` and `/logging`. The first one represents the main event flow in the system. Where the latter one represents how logs are synchronised across the system.
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

# Additional configuration
## Access control
By default, there is only one user with access to all resources. Every service requires own user with appropriate permissions.

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
Virtual hosts are used to logically separate server structure. There are two virtual hosts in the system: `/main` and `/logging` (TODO). The first one represents the main event flow in the system. Where the latter one represents how logs are synchronised across the system.
# RabbitMQ Message Broker

## How to install
Pull newest rabbitmq image from docker repo:
```
docker pull rabbitmq:latest
```

Create container:
```
docker run -d --hostname rabbit@hostname --name rabbit -p 15672:15672 -p 5672:5672 rabbitmq:latest
```
where hostname = `rabbit@hostname` and container name = `rabbit`.

Copy the definition file to container:
```
docker cp definitions.json rabbit:/etc/rabbitmq
```

Connect to container's terminal:
```
docker exec -it rabbit /bin/bash
```

Import definision:
```
rabbitmqctl import_definitions /etc/rabbitmq/definitions.json
```

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

## SSL
```python
# Disable plain TCP connection
listeners.tcp = none

listeners.ssl.default = 5671

ssl_options.cacertfile = /path/to/ca_certificate.pem
ssl_options.certfile   = /path/to/server_certificate.pem
ssl_options.keyfile    = /path/to/server_key.pem

# Demand a certificate from the client
# And fail if the certifacate cannot be verified
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = true
```

Path to RabbitMQ config file: `/etc/rabbitmq/conf.d/rabbitmq.conf`
passphrase: SSL0909@awvmo

Generate private key with RSA:
```
openssl genrsa -des3 -out root.key 2048
```

Generate CA with private key:
```
openssl req -x509 -new -nodes -key root.key -sha256 -out ca-root.pem
```

Generate certificate signing request CSR for RabbitMQ:
```
openssl req -new -key rabbitmq.key -out rabbitmq.csr
```

Generate certificate CRT for RabbitMQ:
```
openssl x509 -req -in rabbitmq.csr -CA ca-root.pem -CAkey root.key -CAcreateserial -out rabbitmq.crt -days 3600 -sha256 -extfile rabbitmq.ext
```
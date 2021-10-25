FROM rabbitmq:latest
LABEL description="Articles RabbitMQ Image" version="0.0.1"

# Add ssl files 
ADD ssl /var/lib/rabbitmq/ssl

# Add predefined definitions
ADD definitions.json /etc/rabbitmq/definitions.json

# Add config file
ADD rabbitmq.conf /etc/rabbitmq/conf.d/rabbitmq.conf
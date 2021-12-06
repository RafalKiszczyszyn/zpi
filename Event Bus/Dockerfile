FROM rabbitmq:latest
LABEL description="ZPI RabbitMQ Image" version="0.0.1"

# Add ssl files 
ADD ssl /var/lib/rabbitmq/ssl

# Add scripts
ADD definitions.json /var/lib/rabbitmq/definitions.json

# Add config file
ADD rabbitmq.conf /etc/rabbitmq/conf.d/rabbitmq.conf

# Enable management plugin
RUN rabbitmq-plugins enable --offline rabbitmq_management
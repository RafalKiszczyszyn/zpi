FROM rabbitmq:latest
LABEL description="ZPI RabbitMQ Image" version="0.0.1"

# Add ssl files 
ADD ssl /var/lib/rabbitmq/ssl

# Add scripts
ADD scripts /var/lib/rabbitmq/scripts

# Add config file
ADD rabbitmq.conf /etc/rabbitmq/conf.d/rabbitmq.conf